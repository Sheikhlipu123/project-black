import React from 'react'

import ProjectComment from './ProjectComment.jsx';
import ProjectScope from './ProjectScope.jsx';

class ProjectDetailsPage extends React.Component {

	constructor(props) {
		super(props);
	}

	render() {
		return (
			<div>
				<h2>Project project_name </h2>
				<br />
				<ProjectComment commentInput={this.props.commentInput}
								onCommentInputChange={this.props.onCommentInputChange}
								commentSubmitted={this.props.commentSubmitted} 

								project={this.props.project}/>
				<hr />
				<ProjectScope newScopeInput={this.props.newScopeInput}
							  handleNewScopeChange={this.props.handleNewScopeChange}
							  onNewScopeClick={this.props.onNewScopeClick} 

							  deleteScope={this.props.deleteScope}
							  scopes={this.props.scopes} />
			</div>
		)
	}

}


export default ProjectDetailsPage;