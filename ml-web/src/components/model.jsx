import React, { Component } from 'react';

class Model extends Component {
	state = {};

	render() {
		console.log('This model: ' + this.props.modelName);
		return (
			<h1 onClick={() => this.props.trainFunc(this.props.modelName, this.props.datasetLocation)}>
				{this.props.modelName}
			</h1>
		);
	}
}

export default Model;
