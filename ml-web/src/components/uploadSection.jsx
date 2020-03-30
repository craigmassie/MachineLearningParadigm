import React, { Component } from 'react';
import Dropzone from 'react-dropzone';
import { BounceLoader } from 'react-spinners';
import { BlobServiceClient, StorageSharedKeyCredential } from '@azure/storage-blob';
import Models from './models';
import { SAS } from '../constants/constants';

class UserUploader extends Component {
	state = {
		uploaderVisibility: true,
		uploadedDatatype: '',
		azureBlobService: {},
		containerClient: {},
		availableModels: [],
		datasetLocation: ''
	};

	componentDidMount() {
		this.initAzureBlobService();
	}

	determineAvailableModels(fileExtension) {
		const imageTypes = [ 'jpg', 'png', 'bmp', 'gif' ];
		if (imageTypes.indexOf(fileExtension) >= 0) {
			return 'image';
		} else {
			return 'whatever else';
		}
	}

	fileExtensionExtract(filename) {
		return filename.split('.').pop();
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
		await this.initContainerClient();
		const currExtension = this.fileExtensionExtract(file.name);
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
	}

	searchingHandler() {
		this.props.nowSearching();
		this.setState({ uploaderVisibility: !this.state.uploaderVisibility });
		this.listAvailableModels();
	}

	async listAvailableModels() {
		const n_containerClient = await this.state.azureBlobService.getContainerClient('testuploads');
		const blobsRet = await n_containerClient.listBlobHierarchySegment('data/');
		const modelArr = blobsRet['Blobs']['Blob'].map((blob) => blob['Name']).filter((blob) => blob.endsWith('.h5'));
		this.setState({ availableModels: modelArr });
	}

	render() {
		return (
			<React.Fragment>
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
						<BounceLoader />
						<p id="searchPlaceholder">Searching for models of type: {this.state.uploadedDatatype}</p>
					</div>
				)}
				<button id="fabNext" onClick={() => this.searchingHandler()}>
					Next
				</button>
				<Models availableModels={this.state.availableModels} datasetLocation={this.state.datasetLocation} />
			</React.Fragment>
		);
	}
}

export default UserUploader;
