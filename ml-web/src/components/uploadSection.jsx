import React, { Component } from 'react';
import Dropzone from 'react-dropzone';
import { BounceLoader } from 'react-spinners';
import { BlobServiceClient, StorageSharedKeyCredential } from '@azure/storage-blob';
import Models from './models';
import { SAS } from '../constants/constants';
import { fileExtensionExtract, fileNameExtract, createJsonPayload, fileCurrentDirectory } from '../helpers/helper';
import { POST_URL } from '../constants/constants';
import ReactMarkdown from 'react-markdown';

class UserUploader extends Component {
	state = {
		uploaderVisibility: true,
		uploadedDatatype: '',
		azureBlobService: {},
		containerClient: {},
		availableModels: {},
		datasetLocation: '',
		modelSelected: {}
	};

	constructor() {
		super();
		this.loadModelDetails = this.loadModelDetails.bind(this);
	}

	async componentDidMount() {
		await this.initAzureBlobService();
		await this.initContainerClient();
	}

	trainModel(modelLocation, datasetLocation, blobFuse = true) {
		if (blobFuse) {
			modelLocation = '/mnt/blobfusetmp/' + modelLocation;
			datasetLocation = '/mnt/blobfusetmp/' + datasetLocation;
			datasetLocation = '/mnt/blobfusetmp/data/mlweb-supplied/initial-test/';
			console.log(datasetLocation);
		}

		var xhr = new XMLHttpRequest();

		xhr.addEventListener('readystatechange', function() {
			if (this.readyState === 4) {
				console.log(this.responseText);
			}
		});

		xhr.open('POST', 'https://mlwebtrain.azurewebsites.net/trainModel');
		xhr.setRequestHeader('Content-Type', 'application/json');
		const jsonPayload = JSON.stringify(createJsonPayload(modelLocation, datasetLocation, 1));
		xhr.send(jsonPayload);
		console.log(jsonPayload);
		return xhr.responseText;
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

	initAzureBlobService = async () => {
		/*
		 * Initialises the Azure Blob Service connection and saves to the current application state.
		 */
		try {
			console.log(process.env.REACT_APP_AZURE_STORAGE_ACCOUNT);
			const blobServiceClient = new BlobServiceClient(
				`https://${process.env.REACT_APP_AZURE_STORAGE_ACCOUNT}.blob.core.windows.net${SAS}`
			);
			this.setState({ azureBlobService: blobServiceClient });
		} catch (err) {
			throw `Failed to initialise Azure Blob Service connection. Please check the provided storage account and key is correct. ${err}`;
		}
	};

	initContainerClient = async () => {
		try {
			const azureBlobService = this.state.azureBlobService;
			const containerName = process.env.REACT_APP_AZURE_CONTAINER_NAME;
			const n_containerClient = await azureBlobService.getContainerClient(containerName);
			this.setState({ containerClient: n_containerClient });
		} catch (err) {
			throw `Failed to initialise Azure Blob Service connection. Please check the provided container name is correct. ${err}`;
		}
	};

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
			const file_name = `data/user-supplied/${Date.now()}_${file.name}`;
			this.setState({ datasetLocation: file_name });
			// Get a block blob client
			const blockBlobClient = this.state.containerClient.getBlockBlobClient(file_name);

			const uploadBlobResponse = await blockBlobClient.upload(file, file.size);

			console.log('Blob was uploaded successfully. requestId: ', uploadBlobResponse.requestId);
		} else {
			console.log('.zip must be passed to web application.');
		}
		this.setState({ uploadedDatatype: this.determineAvailableModels('jpg') });
		this.searchingHandler();
	}

	async downloadModelInfo(modelLocation) {
		if (!this.state.containerClient) {
			return;
		}
		const infoFile = fileCurrentDirectory(modelLocation) + '/info.txt';
		console.log(infoFile);
		const blobClient = this.state.containerClient.getBlockBlobClient(infoFile);
		const downloadBlockBlobResponse = await blobClient.download();
		const downloaded = await this.blobToString(await downloadBlockBlobResponse.blobBody);
		return downloaded;
	}

	async downloadArchitectureInfo(architecture) {
		const infoFile = `models/mlweb-supplied/${architecture}/info.txt`;
		console.log(infoFile);
		const blobClient = this.state.containerClient.getBlockBlobClient(infoFile);
		const downloadBlockBlobResponse = await blobClient.download();
		const downloaded = await this.blobToString(await downloadBlockBlobResponse.blobBody);
		return downloaded;
	}

	async blobToString(blob) {
		const fileReader = new FileReader();
		return new Promise((resolve, reject) => {
			fileReader.onloadend = (ev) => {
				resolve(ev.target.result);
			};
			fileReader.onerror = reject;
			fileReader.readAsText(blob);
		});
	}

	async listAvailableModels() {
		const n_containerClient = await this.state.azureBlobService.getContainerClient('testuploads');
		const blobsRet = await n_containerClient.listBlobHierarchySegment('data/');
		const modelArr = blobsRet['Blobs']['Blob'].map((blob) => blob['Name']).filter((blob) => blob.endsWith('.h5'));
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

	searchingHandler() {
		this.setState({ uploaderVisibility: !this.state.uploaderVisibility });
		this.listAvailableModels();
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
												<p>Drag 'n' drop train dataset here, or click to select folder</p>
											</div>
										</section>
									)}
								</Dropzone>
							</div>
						) : (
							<div>
								{this.state.availableModels ? (
									<section>{modelArchs}</section>
								) : (
									<section>
										<BounceLoader />
										<p id="searchPlaceholder">
											Searching for models of type: {this.state.uploadedDatatype}
										</p>
									</section>
								)}
							</div>
						)}
						<button id="fabNext" onClick={() => this.searchingHandler()}>
							Next
						</button>
					</div>
				) : (
					<div class="modelCard">
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
