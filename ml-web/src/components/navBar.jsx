import React, { Component } from 'react';

class NavBar extends Component {
	state = {};
	render() {
		return (
			<div className="navBar">
				<ul id="nav">
					<li>
						<a href="/">Home</a>
					</li>
					<li>
						<a href="/training">Models Training</a>
					</li>
				</ul>
			</div>
		);
	}
}

export default NavBar;
