import React, { Component } from 'react';
import Dropzone from 'react-dropzone';
import { BounceLoader } from 'react-spinners';
import { BlobServiceClient, StorageSharedKeyCredential } from '@azure/storage-blob';
import Models from './models';
import { SAS } from '../constants/constants';
import {
	fileExtensionExtract,
	createJsonPayload,
	fileCurrentDirectory,
	blobToString,
	getParentDirectory
} from '../helpers/helper';
import { POST_URL } from '../constants/constants';
import ReactMarkdown from 'react-markdown';

const AUTOML_PLACEHOLDER_FILE = 'ph.h5';
class UserUploader extends Component {
	state = {
		uploaderVisibility: true,
		uploadedDatatype: '',
		availableModels: {},
		datasetLocation: '',
		modelSelected: {}
	};

	constructor() {
		super();
		this.loadModelDetails = this.loadModelDetails.bind(this);
	}

	async trainModel(modelLocation, datasetLocation, blobFuse = true) {
		if (blobFuse) {
			modelLocation = '/mnt/blobfusetmp/' + modelLocation;
			datasetLocation = '/mnt/blobfusetmp/' + datasetLocation;
			console.log(datasetLocation);
		}

		var jsonPayload;
		// If the "model" we're training on is actually the placeholder for AutoML
		if (modelLocation.endsWith(AUTOML_PLACEHOLDER_FILE)) {
			modelLocation = fileCurrentDirectory(modelLocation);
			jsonPayload = JSON.stringify(createJsonPayload(modelLocation, datasetLocation, 5, 'ImageClassifier', 1));
		} else {
			jsonPayload = JSON.stringify(createJsonPayload(modelLocation, datasetLocation, 5));
		}

		var xhr = new XMLHttpRequest();

		xhr.addEventListener('readystatechange', function() {
			if (this.readyState === 4) {
				console.log(this.responseText);
			}
		});

		console.log(jsonPayload);
		// xhr.open('POST', 'https://mlwebtrain.azurewebsites.net/trainModel');
		// xhr.open('POST', 'http://0.0.0.0:5000/trainModel');
		// xhr.setRequestHeader('Content-Type', 'application/json');
		// xhr.send(jsonPayload);
		// const resp = xhr.responseText;
		// console.log(resp);
		// return resp;
	}

	async loadModelDetails(modelLocation, modelDescription) {
		const modelDesc = await this.downloadModelInfo(modelLocation);
		this.setState({ modelSelected: { modelName: modelLocation, modelDescription: modelDesc } });
	}

	determineAvailableModels(fileExtension) {
		const imageTypes = [ 'jpg', 'png', 'bmp', 'gif' ];
		if (imageTypes.indexOf(fileExtension) >= 0) {
			return 'image';
		} else {
			return 'whatever else';
		}
	}

	async handleDrop(acceptedFiles) {
		const fileExtension = 'zip';
		const reader = new FileReader();
		reader.onabort = () => console.log('file reading was aborted');
		reader.onerror = () => console.log('file reading has failed');
		reader.onload = () => {
			const binaryStr = reader.result;
		};
		const file = acceptedFiles[0];
		const currExtension = fileExtensionExtract(file.name);
		if (currExtension == fileExtension) {
			const file_name = `data/user-supplied/${file.name}`;
			this.setState({ datasetLocation: file_name });
			// Get a block blob client
			const blockBlobClient = this.props.containerClient.getBlockBlobClient(file_name);
			this.setState({ uploaderVisibility: !this.state.uploaderVisibility });
			const uploadBlobResponse = await blockBlobClient.upload(file, file.size);

			console.log('Blob was uploaded successfully. requestId: ', uploadBlobResponse.requestId);
		} else {
			console.log('.zip must be passed to web application.');
		}
		this.setState({ uploadedDatatype: this.determineAvailableModels('jpg') });
		this.searchingHandler();
	}

	async downloadModelInfo(modelLocation) {
		if (!this.props.containerClient) {
			return;
		}
		const infoFile = fileCurrentDirectory(modelLocation) + '/info.txt';
		console.log(infoFile);
		const blobClient = this.props.containerClient.getBlockBlobClient(infoFile);
		const downloadBlockBlobResponse = await blobClient.download();
		const downloaded = await blobToString(await downloadBlockBlobResponse.blobBody);
		return downloaded;
	}

	async downloadArchitectureInfo(architecture) {
		const infoFile = `models/mlweb-supplied/${architecture}/info.txt`;
		console.log(infoFile);
		const blobClient = this.props.containerClient.getBlockBlobClient(infoFile);
		const downloadBlockBlobResponse = await blobClient.download();
		const downloaded = await blobToString(await downloadBlockBlobResponse.blobBody);
		return downloaded;
	}

	isUserDefined(model) {
		const modelArr = model.split('-');
		return (
			modelArr.length === 5 &&
			modelArr[0].length === 8 &&
			modelArr[1].length === 4 &&
			modelArr[2].length === 4 &&
			modelArr[3].length === 4 &&
			modelArr[4].length === 12
		);
	}

	async listAvailableModels() {
		const n_containerClient = await this.props.azureBlobService.getContainerClient('testuploads');
		const blobsRet = await n_containerClient.listBlobHierarchySegment('', undefined, {
			prefix: 'models/mlweb-supplied/'
		});
		const modelArr = blobsRet['Blobs']['Blob']
			.map((blob) => blob['Name'])
			.filter((blob) => blob.endsWith('.h5'))
			.filter((blob) => !this.isUserDefined(getParentDirectory(blob)));
		const modelTypes = modelArr.map((model) => model.split('/')[2]);
		var res = {};
		for (var i in modelTypes) {
			const key = modelTypes[i];
			if (key in res) {
				res[key]['models'].push(modelArr[i]);
			} else {
				const archInfo = await this.downloadArchitectureInfo(key);
				res[key] = { info: archInfo, models: [ modelArr[i] ] };
			}
		}
		this.setState({ availableModels: res });
		console.log(res);
	}

	async searchingHandler() {
		await this.listAvailableModels();
	}

	render() {
		const modelArchs = [];
		if (this.state.availableModels != {}) {
			let i = 0;
			for (const key in this.state.availableModels) {
				let model_arch = key.replace(/-/g, ' ');
				modelArchs.push(
					<Models
						key={i}
						architecture={model_arch}
						architectureInfo={this.state.availableModels[key]['info']}
						models={this.state.availableModels[key]['models']}
						trainFunc={this.loadModelDetails}
						parentName={true}
					/>
				);
				++i;
			}
		}
		return (
			<React.Fragment>
				{Object.keys(this.state.modelSelected).length === 0 &&
				this.state.modelSelected.constructor === Object ? (
					<div>
						{this.state.uploaderVisibility ? (
							<div className="uploadDiv">
								<Dropzone onDrop={(acceptedFiles) => this.handleDrop(acceptedFiles)}>
									{({ getRootProps, getInputProps }) => (
										<section id="uploadSection">
											<div {...getRootProps()}>
												<input {...getInputProps()} />
												<p>Drag 'n' drop dataset here, or click to select zip file</p>
											</div>
										</section>
									)}
								</Dropzone>
							</div>
						) : (
							<div>
								{Object.keys(this.state.availableModels).length === 0 &&
								this.state.availableModels.constructor === Object ? (
									<section>
										<BounceLoader />
									</section>
								) : (
									<section className="modelArchs">{modelArchs}</section>
								)}
							</div>
						)}
						{/* <button id="fabNext" onClick={() => this.searchingHandler()}>
							Next
						</button> */}
					</div>
				) : (
					<div className="modelCard">
						<ReactMarkdown source={this.state.modelSelected['modelDescription']} />
						<button
							id="fabTrain"
							onClick={() =>
								this.trainModel(this.state.modelSelected['modelName'], this.state.datasetLocation)}
						>
							Train
						</button>
					</div>
				)}
			</React.Fragment>
		);
	}
}

export default UserUploader;
