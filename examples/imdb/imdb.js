let {Grid, Col, Row, Label, Table, ListGroup, ListGroupItem} = require('react-bootstrap');
let $ = require('jquery');
const KEEN = 'https://cdn.rawgit.com/keen/dashboards/gh-pages/assets/css/keen-dashboards.css';
$('head').append(`<link rel="stylesheet" type="text/css" href="${KEEN}" />`);
$('body').addClass('application');
let React = require('react');
let _ = require('underscore');
let BindableComponent = require('translucent/components/bindable');
let Select = require('translucent/components/select');

class Frame extends React.Component {
    render() {
        return (
            <div className="chart-wrapper">
                {this.props.title ? <div className="chart-title">{this.props.title}</div> : ''}
                <div className="chart-stage">{this.props.children}</div>
                {this.props.notes ? <div className="chart-notes">{this.props.notes}</div> : ''}
            </div>
        );
    }
}

class ListBox extends BindableComponent {
    handleClick(value) {
        if (value !== this.state.value) {
            React.findDOMNode(this.refs[value]).classList.add('active');
            React.findDOMNode(this.refs[this.state.value]).classList.remove('active');
            this.onValueChange(value);
        }
    }

    componentDidUpdate() {
        const selected = React.findDOMNode(this.refs[this.state.value]);
        const parent = React.findDOMNode(this.refs.parent);

        const top = $(selected).position().top;
        const bottom = top + $(selected).height();
        const parentTop = 0;
        const parentBottom = parentTop + $(parent).height();

        console.log(top, bottom, $(parent).height(), $(parent).outerHeight());
        console.log(selected.offsetTop, selected.offsetHeight);

        if (bottom < parentTop || top > parentBottom) {
            selected.scrollIntoView();
        }
    }

    render() {
        const items = this.props.items.map(item =>
            <ListGroupItem href="#" ref={item.value} active={this.state.value === item.value}
                           key={item.value} onClick={this.handleClick.bind(this, item.value)}>
                {item.label}
            </ListGroupItem>
        );
        return (
            <ListGroup ref="parent" className={this.props.className}>
                {items}
            </ListGroup>
        );
    }
}

class ListItem extends React.Component {
    render() {
        return (
            <div>
                <img src={this.props.title.image} />
                <div className="content">
                    <h6>{this.props.title.title}</h6>
                    <p className="small">
                        Year: {this.props.title.year}<br/>
                        Rating: {this.props.title.rating}
                    </p>
                </div>
            </div>
        );
    }
}

class Sidebar extends React.Component {
    render() {
        const titles = this.props.titles,
            options = titles.map(t => ({value: t.id, label: `${t.title} (${t.year})`})),
            items = titles.map(t => ({value: t.id, label: <ListItem title={t}/>}));
        return (
            <Frame>
                <Select options={_.sortBy(options, 'label')} bind="selected" clearable={false}/>
                <ListBox className="title-list" items={items} bind="selected"/>
            </Frame>
        );
    }
}

class Details extends React.Component {
    render() {
        const title = this.props.title;
        const genres = _.flatten(title.genres.map(genre =>
                                 [<Label bsStyle="primary">{genre}</Label>, ' ']));
        const certificate = <Label bsStyle="success">{title.certificate.certificate}</Label>;
        const tagline = title.tagline ? <blockquote><p>{title.tagline}</p></blockquote> : '';
        return (
            <Frame>
                <div className="lead">
                    {title.title} <small className="muted">({title.year})</small>
                </div>
                <hr/>
                <img src={title.image.url.replace('_V1_', '_V1_SX214_AL_')} />
                <div className="content">
                    <p>{genres} {certificate}</p>
                    <Table>
                        <tr><td>Release date</td><td>{title.release_date.normal}</td></tr>
                        <tr><td>IMDB Rating</td><td>{title.rating} ({title.num_votes} votes)</td></tr>
                        <tr><td>Runtime</td><td>{title.runtime.time / 60} min</td></tr>
                    </Table>
                    <p>{title.plot.outline}</p>
                </div>
            </Frame>
        );
    }
}

class Page extends React.Component {
    render() {
        return (
            <Grid className="parent">
                <Row>
                    <Col sm={4}>
                        <Sidebar titles={this.props.env.titles}/>
                    </Col>
                    <Col sm={8} className="details">
                        <Details title={this.props.env.title} />
                    </Col>
                </Row>
            </Grid>
        );
    }
}

Translucent.render(env => <Page env={env} />);
