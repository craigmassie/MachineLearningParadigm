import React, { Component } from 'react';
import Model from './model';
import { POST_URL } from '../constants/constants';
import { createJsonPayload } from '../helpers/helper';

class Models extends Component {
	state = {};

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

	render() {
		if (this.props.availableModels) {
			const availableModels = this.props.availableModels.map((m, index) => (
				<Model
					key={index}
					modelName={m}
					trainFunc={this.trainModel}
					datasetLocation={this.props.datasetLocation}
				/>
			));
			return availableModels;
		}
	}
}

export default Models;
