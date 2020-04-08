import React, { Component } from 'react';
import Models from './models';
import { blobToString, fileCurrentDirectory, fileNameExtract } from '../helpers/helper';
import { Label, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import Iframe from 'react-iframe';

class Training extends Component {
	state = {
		displayUploader: true,
		containerClient: {},
		modelListing: {},
		modelCards: {},
		completeModels: {},
		currentModel:'',
		numComplete: 0,
		history: [],
		downloadURL: '#',
		netronURL: '#',
		testImageURL:'https://www.nynmedia.com/sites/default/files/all/nyn-placeholder-250x250.png',
		currentPred:"",
		explain: false,
	};

	constructor() {
		super();
		this.displayModelInfo = this.displayModelInfo.bind(this);
		this.listCompleteModels = this.listCompleteModels.bind(this);
		this.handleClick = this.handleClick.bind(this);
		this.explainImg = this.explainImg.bind(this);
		this.checkForExplanation = this.checkForExplanation.bind(this);
	}

	async componentDidMount() {
		await this.initAzure();
		this.listCompleteModels();
		setInterval(this.listCompleteModels, 30000);
		this.checkForExplanation();
		setInterval(this.checkForExplanation, 10000);
	}

	async initAzure() {
		const containerClient = await this.props.azureBlobService.getContainerClient('testuploads');
		const models = await containerClient.listBlobHierarchySegment('', undefined, {
			prefix: 'models/mlweb-supplied/'
		});
		this.setState((prevState) => ({
			containerClient: containerClient,
			modelListing: models
		}));
		this.listTrainingModels();
	}

	async listCompleteModels() {
		if (Object.keys(this.state.modelListing).length === 0 && this.state.modelListing.constructor === Object) {
			return;
		} else {
			const trainingModelsArr = this.state.modelListing?.Blobs?.Blob.map((blob) => blob?.Name).filter((blob) => blob.endsWith('history.json'));
			console.log(trainingModelsArr);
			const trainedModels = (
				<Models
					architecture={'Complete'}
					architectureInfo={'Models that have finished training.'}
					models={trainingModelsArr}
					trainFunc={this.displayModelInfo}
					parentName={true}
				/>
			);
			//If we have found another completed model, list the current training models again to remove completed.
			if (trainingModelsArr.length >= this.state.numComplete) {
				this.setState({ numComplete: trainingModelsArr.length });
				this.listTrainingModels();
			}
			this.setState({ completeModels: trainedModels });
		}
	}

	async checkForExplanation(){
		var requestOptions = {
			method: 'GET',
			redirect: 'follow'
		};
		if (Object.keys(this.state.containerClient).length === 0 && this.state.containerClient.constructor === Object) {
			return;
		}
		if (this.state.currentModel.length === 0){
			return;
		}
		const outputTest = fileCurrentDirectory(this.state.currentModel) + "/output.png";
		const modelBlobClient = this.state.containerClient.getBlockBlobClient(outputTest);
		fetch(modelBlobClient?.url, requestOptions)
			.then(response => {
				(response.status == 200 && this.state.explain && this.setState({testImageURL : modelBlobClient.url}));
			});
	}

	convertToTimeSeries(history) {
		var ret = [];
		var length = history.loss.length;
		for (let i = 0; i < length; i++) {
			let curr = {};
			for (var key in history) {
				if (history.hasOwnProperty(key)) {
					curr[key] = history[key][i];
				}
			}
			ret.push(curr);
		}
		return ret;
	}

	async displayModelInfo(historyFile) {
		if (!this.props.containerClient) {
			return;
		}
		const blobClient = this.props.containerClient.getBlockBlobClient(historyFile);
		const downloadBlockBlobResponse = await blobClient.download();
		let downloaded = await blobToString(await downloadBlockBlobResponse.blobBody);
		const jsonDownloaded = JSON.parse(downloaded);
		const history = this.convertToTimeSeries(jsonDownloaded);
		const dir = fileCurrentDirectory(historyFile);
		const model_location = dir + '/' + fileNameExtract(dir) + '.h5';
		const modelBlobClient = this.props.containerClient.getBlockBlobClient(model_location);
		this.setState({currentModel: model_location, history : history, downloadURL: modelBlobClient?.url, netronURL : "https://lutzroeder.github.io/netron/?url=" + encodeURIComponent(modelBlobClient?.url) + "&identifier=" + fileNameExtract(dir) + '.h5'})
	}

	async listTrainingModels() {
		const trainingModelsArr = this.state.modelListing?.Blobs?.Blob.map((blob) => blob?.Name).filter((blob) => blob.endsWith('trainingInfo.txt'));
		if (trainingModelsArr !== undefined && trainingModelsArr.length > 0) {
			const modelArch = (
				<Models
					architecture={'Training'}
					architectureInfo={'Models currently in the training process.'}
					models={trainingModelsArr}
					trainFunc={this.displayModelInfo}
					parentName={true}
				/>
			);
			console.log(modelArch);
			this.setState({ modelCards: modelArch });
		}
	}

	handleChange = (e) => {
		this.setState({
		  testImageURL: e.target.value
		})
	  }

	formatPredictionResults(result){
		var txt = "";
		Object.keys(result).forEach(function(key) {
			txt += `${key}: ${Number(result[key] * 100).toFixed(2)}%\n`;
		  });
		this.setState({currentPred : txt});
	}

	handleClick(blobfuse=true){
		this.setState({currentPred : ""});
		var myHeaders = new Headers();
		myHeaders.append("Content-Type", "application/json");
		var raw;
		if (blobfuse){
			raw = JSON.stringify({"model_location":"/mnt/blobfusetmp/"+this.state.currentModel,"image_url":this.state.testImageURL});
		}else{
			raw = JSON.stringify({"model_location":this.state.currentModel,"image_url":this.state.testImageURL});
		}
		var requestOptions = {
			method: 'POST',
			headers: myHeaders,
			body: raw,
			redirect: 'follow'
		  };
		  
		  fetch("https://mlwebtrain.azurewebsites.net/testModel", requestOptions)
			.then(response => response.text())
			.then(result => this.formatPredictionResults(JSON.parse(result)))
			.catch(error => console.log('error', error));
	}

	explainImg(blobfuse=true){
		var myHeaders = new Headers();
		myHeaders.append("Content-Type", "application/json");
		var raw;
		if (blobfuse){
			raw = JSON.stringify({"model_location":"/mnt/blobfusetmp/"+this.state.currentModel,"image_location":"/mnt/blobfusetmp/"+ fileCurrentDirectory(this.state.currentModel) + "/output.png"});
		}else{
			raw = JSON.stringify({"model_location":this.state.currentModel,"image_url":this.state.testImageURL});
		}
		var requestOptions = {
			method: 'POST',
			headers: myHeaders,
			body: raw,
			redirect: 'follow'
		  };
		  
		  fetch("https://mlwebtrain.azurewebsites.net/explainTest", requestOptions)
			.then(response => response.text())
			.then(result => console.log(result))
			.catch(error => console.log('error', error));
		this.setState({explain : true});
	}

	render() {
		return (
			<div>
				{Object.keys(this.state.modelCards).length === 0 && this.state.modelCards.constructor === Object ? (
					<h1 id="noTrain">
						No models currently training. If you just kicked off a process, give us a moment.
					</h1>
				) : (
					<section className="modelsTraining">{this.state.modelCards}</section>
				)}
				{Object.keys(this.state.completeModels).length === 0 &&
				this.state.completeModels.constructor === Object ? null : (
					<section className="modelsTraining">{this.state.completeModels}</section>
				)}
				{this.state.history.length === undefined || this.state.history.length === 0 ? null : (
					<div>
						<LineChart width={400} height={400} data={this.state.history}>
							<CartesianGrid strokeDasharray="3 3" />
							<XAxis>
								<Label dy={12}>Epoch Number</Label>
							</XAxis>
							<YAxis />
							<Tooltip />
							<Legend />
							<Line type="monotone" dataKey="loss" stroke="#8884d8" />
						</LineChart>
						<LineChart width={400} height={400} data={this.state.history}>
							<CartesianGrid strokeDasharray="3 3" />
							<XAxis>
								<Label dy={12}>Epoch Number</Label>
							</XAxis>
							<YAxis />
							<Tooltip />
							<Legend />
							<Line type="monotone" dataKey="accuracy" stroke="#8884d8" />
						</LineChart>
						{/* <Iframe
							url={this.state.netronURL}
							width="450px"
							height="450px"
							id="myId"
							className="myClassname"
							display="initial"
							position="relative"
							allowFullScreen="true"
						/> */}
						<a href={this.state.downloadURL} target="_blank">
							<button>Download Model</button>
						</a>
						<a href={this.state.netronURL} target="_blank">
							<button>Visualise Model on Netron</button>
						</a>
						<input type="text" onChange={this.handleChange}/>
						<button onClick={this.handleClick}>Test Image</button>
						<img id = "predictImg" src={this.state.testImageURL}></img>
						{this.state.currentPred && <button onClick={this.explainImg}>Explain Prediction</button>}
						<p>{this.state.currentPred}</p>
					</div>
				)}
			</div>
		);
	}
}

export default Training;
