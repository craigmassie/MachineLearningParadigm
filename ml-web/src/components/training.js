import React, { Component } from 'react';
import Models from './models';
import { blobToString, fileCurrentDirectory, fileNameExtract } from '../helpers/helper';
import {
	Label, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  } from 'recharts';

class Training extends Component {
	state = {
		displayUploader: true,
		containerClient: {},
		modelListing: {},
		modelCards: {},
		completeModels: {},
		numComplete: 0,
		history:[],
		downloadURL:'#',
	};

	constructor() {
		super();
		this.displayModelInfo = this.displayModelInfo.bind(this);
		this.listCompleteModels = this.listCompleteModels.bind(this);
	}

	async componentDidMount() {
		await this.initAzure();
		this.listCompleteModels();
		setInterval(this.listCompleteModels, 100000);
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
		if (Object.keys(this.state.modelListing).length === 0 && this.state.modelListing.constructor === Object){
			return;
		}else{
			const trainingModelsArr = this.state.modelListing?.Blobs?.Blob.map((blob) => blob?.Name).filter((blob) => blob.endsWith('history.json'));
			console.log(trainingModelsArr)
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
			if (trainingModelsArr.length >= this.state.numComplete){
				this.setState({numComplete : trainingModelsArr.length});
				this.listTrainingModels();
			}
			this.setState({ completeModels: trainedModels });
		}
	}

	convertToTimeSeries(history){
		var ret = [];
		var length = history?.loss.length;
		for(let i = 0; i < length; i++){
			let curr = {};
			for(var key in history){
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
		const history = this.convertToTimeSeries(jsonDownloaded)
		const dir = fileCurrentDirectory(historyFile)
		const model_location = dir + '/' + fileNameExtract(dir) + '.h5';
		const modelBlobClient = this.props.containerClient.getBlockBlobClient(model_location);
		this.setState({downloadURL : "https://lutzroeder.github.io/netron/?url=" + encodeURIComponent(modelBlobClient?.url)})
		this.setState({history : history});
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

	render() {
		return (
			<div>
			{Object.keys(this.state.modelCards).length === 0 && this.state.modelCards.constructor === Object
			  ? <h1 id="noTrain">No models currently training. If you just kicked off a process, give us a moment.</h1>
			  :  <section className="modelsTraining">{this.state.modelCards}</section>
			}
			{Object.keys(this.state.completeModels).length === 0 && this.state.completeModels.constructor === Object
			  ? null
			  :  <section className="modelsTraining">{this.state.completeModels}</section>
			}
			{this.state.history.length === undefined || this.state.history.length === 0
			? null
			: <div>
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
			<a href={this.state.downloadURL} target="_blank">
    		<button>Download Model</button>
			</a>
			<a href="https://lutzroeder.github.io/netron/" target="_blank">
    		<button>Visualise Model on Netron</button>
			</a>
			</div>
			}
		
		  </div>
		);
	}
}

export default Training;
