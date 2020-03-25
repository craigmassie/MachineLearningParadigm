import React, { Component } from 'react';
import Dropzone from 'react-dropzone';
import { BounceLoader } from 'react-spinners';
import { BlobServiceClient, StorageSharedKeyCredential } from '@azure/storage-blob';

class UserUploader extends Component {
	state = {
		uploaderVisibility: true,
		uploadedDatatype: '',
		azureBlobService: {},
		containerClient: {}
	};

	componentDidMount() {
		this.initAzureBlobService();
	}

	determineAvailableModels(fileExtension) {
		let imageTypes = [ 'jpg', 'png', 'bmp', 'gif' ];
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
			var sas =
				'?sv=2018-03-28&ss=bfqt&srt=sco&sp=rwl&st=2020-03-25T22%3A55%3A03Z&se=2020-03-28T22%3A55%3A00Z&sig=pzowXst9KtSAVxtF3Vyi1ysI55Ikb8AHvVFHEEbvB8I%3D';
			console.log(process.env.REACT_APP_AZURE_STORAGE_ACCOUNT);
			const blobServiceClient = new BlobServiceClient(
				`https://${process.env.REACT_APP_AZURE_STORAGE_ACCOUNT}.blob.core.windows.net${sas}`
			);
			this.setState({ azureBlobService: blobServiceClient });
		} catch (err) {
			throw `Failed to initialise Azure Blob Service connection. Please check the provided storage account and key is correct. ${err}`;
		}
	};

	initContainerClient = async () => {
		try {
			var azureBlobService = this.state.azureBlobService;
			var containerName = process.env.REACT_APP_AZURE_CONTAINER_NAME;
			const n_containerClient = await azureBlobService.getContainerClient(containerName);
			this.setState({ containerClient: n_containerClient });
		} catch (err) {
			throw `Failed to initialise Azure Blob Service connection. Please check the provided container name is correct. ${err}`;
		}
	};

	// uploadFile = async (fileName, fileContent) => {
	// 	const blockBlobClient = this.state.containerClient.getBlockBlobClient(fileName);
	// 	const uploadBlobResponse = await blockBlobClient.upload(fileContent, Buffer.byteLength(fileContent));
	// };

	async handleDrop(acceptedFiles) {
		let fileExtension = 'zip';
		const reader = new FileReader();
		reader.onabort = () => console.log('file reading was aborted');
		reader.onerror = () => console.log('file reading has failed');
		reader.onload = () => {
			const binaryStr = reader.result;
		};
		var file = acceptedFiles[0];
		await this.initContainerClient();
		let currExtension = this.fileExtensionExtract(file.name);
		if (currExtension == fileExtension) {
			console.log(this.state.containerClient);

			var data = reader.readAsBinaryString(file);

			console.log(data);

			// Get a block blob client
			const blockBlobClient = this.state.containerClient.getBlockBlobClient(file.name);

			const uploadBlobResponse = await blockBlobClient.upload(file, file.size);

			console.log('Blob was uploaded successfully. requestId: ', uploadBlobResponse.requestId);
		} else {
			console.log('Inconsistent data types passed to web app.');
		}
		this.setState({ uploadedDatatype: this.determineAvailableModels('jpg') });
	}

	searchingHandler() {
		this.props.nowSearching();
		this.setState({ uploaderVisibility: !this.state.uploaderVisibility });
	}

	listAvailableModels() {}

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
					<li id="models" />
				</button>
			</React.Fragment>
		);
	}
}

export default UserUploader;
