import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import NavBar from './components/navBar';
import { connect } from 'react-redux';
import UserUploader from './components/uploadSection';
import { useState } from 'react';

class App extends Component {
	nowSearching() {
		console.log('now searching');
	}

	state = {
		displayUploader: true
	};
	render() {
		return (
			<div className="App">
				<NavBar />
				<UserUploader vis={this.state.displayUploader} nowSearching={() => this.nowSearching()} />
			</div>
		);
	}
}

export default App;
