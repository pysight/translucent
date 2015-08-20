req(['react-bootstrap', 'jquery'], () => {
    let {Grid, Col, Row, Panel, Label, Table, ListGroup, ListGroupItem} = ReactBootstrap;

    const KEEN = 'https://cdn.rawgit.com/keen/dashboards/gh-pages/assets/css/keen-dashboards.css';
    $('head').append(`<link rel="stylesheet" type="text/css" href="${KEEN}" />`);
    $('body').addClass('application');

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
            if (value != this.state.value) {
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
            const parent_top = 0;
            const parent_bottom = parent_top + $(parent).height();

            console.log(top, bottom, $(parent).height(), $(parent).outerHeight());
            console.log(selected.offsetTop, selected.offsetHeight);

            if (bottom < parent_top || top > parent_bottom) {
                selected.scrollIntoView();
            }
        }

        render() {
            const items = _.map(this.props.items, item =>
                <ListGroupItem href="#" ref={item.value}  active={this.state.value == item.value}
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

    class ListItem2 extends React.Component {
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

    class Sidebar2 extends React.Component {
        render() {
            const titles = this.props.titles,
                  options = _.map(titles, t => ({value: t.id, label: `${t.title} (${t.year})`})),
                  items = _.map(titles, t => ({value: t.id, label: <ListItem2 title={t}/>}));
            return (
                <Frame>
                    <Select options={_.sortBy(options, 'label')} bind="selected" clearable={false}/>
                    <ListBox className="title-list" items={items} bind="selected"/>
                </Frame>
            )
        }
    }

    class ListItem extends React.Component {
        onSelect() {
            if (this.props.active) {
                return;
            }
            React.findDOMNode(this.refs[this.props.title.id]).classList.add('active');
            const activeItem = this.props.activeItem();
            if (activeItem) {
                React.findDOMNode(activeItem).classList.remove('active');
            }
            Translucent.update('selected', this.props.title.id);
        }

        render() {
            const t = this.props.title;
            const cls = classNames('list-group-item', {active: this.props.active});
            return (
                <a className={cls} key={t.id} href="#" ref={t.id} onClick={this.onSelect.bind(this)}>
                    <img src={t.image} />
                    <div className="content">
                        <h6>{t.title}</h6>
                        <p className="small">
                            Year: {t.year}<br/>
                            Rating: {t.rating}
                        </p>
                    </div>
                </a>
            );
        }
    }

    class Sidebar extends React.Component {
        onSelect(value) {
            if (this.refs[value]) {
                React.findDOMNode(this.refs[value]).scrollIntoView();
            }
        }

        render() {
            const titles = _.map(this.props.titles,
                t => <ListItem active={t.id == this.props.selected} title={t} key={t.id}
                               ref={t.id} activeItem={() => this.refs[this.props.selected]}/>);
            const options = _.sortBy(_.map(this.props.titles,
                t => ({value: t.id, label: `${t.title} (${t.year})`})), 'label');
            return (
                <Frame>
                    <Select options={options} bind="selected" clearable={false}
                            onChange={this.onSelect.bind(this)}/>
                    <div className="list-group title-list">
                        {titles}
                    </div>
                </Frame>
            );
        }
    }

    class Details extends React.Component {
        render() {
            const title = this.props.title;
            const frame_title = (
                <span>
                    <strong>{title.title}</strong>
                    <small className="muted"> ({title.year})</small>
                </span>
            );
            const genres = _.flatten(_.map(title.genres, genre =>
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
            // Sidebar titles={this.props.titles} selected={this.props.env.selected}
            return (
                <Grid className="parent">
                    <Row>
                        <Col sm={4}>
                            <Sidebar2 titles={this.props.env.titles}/>
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
});

