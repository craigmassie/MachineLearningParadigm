import React, { Component } from 'react';
import './App.css';
import NavBar from './components/navBar';
import UserUploader from './components/uploadSection';
import Training from './components/training';
import { BrowserRouter, Route, Switch } from 'react-router-dom';
import { SAS } from './constants/constants';
import { BlobServiceClient, StorageSharedKeyCredential } from '@azure/storage-blob';

class App extends Component {
	nowSearching() {
		console.log('now searching');
	}

	state = {
		azureBlobService: {},
		containerClient: {}
	};

	async componentDidMount() {
		document.title = 'Machine Learning Web';
		await this.initAzureBlobService();
		await this.initContainerClient();
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

	render() {
		if (
			Object.keys(this.state.azureBlobService).length === 0 &&
			this.state.azureBlobService.constructor === Object
		) {
			return null;
		}
		return (
			<BrowserRouter>
				<div>
					<NavBar />
					<Switch>
						<Route
							path="/"
							component={() => (
								<UserUploader
									azureBlobService={this.state.azureBlobService}
									containerClient={this.state.containerClient}
								/>
							)}
							exact
						/>
						<Route
							path="/training"
							component={() => (
								<Training
									azureBlobService={this.state.azureBlobService}
									containerClient={this.state.containerClient}
								/>
							)}
							exact
						/>
						<Route component={Error} />
					</Switch>
				</div>
			</BrowserRouter>
			// <div className="App">

			// 	{/* <UserUploader vis={this.state.displayUploader} nowSearching={() => this.nowSearching()} /> */}
			// </div>
		);
	}
}

export default App;
