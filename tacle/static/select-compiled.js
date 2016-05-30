var Orientation = {
    row: "Row",
    col: "Column",
    none: "None"
};

function exportTables(tables) {
    var converted = [];
    for (var i = 0; i < tables.length; i++) {
        converted.push({
            "Name": "T" + (i + 1),
            "Bounds": tables[i].bounds,
            "Orientation": Orientation[tables[i].orientation]
        });
    }
    return JSON.stringify({ "Tables": converted });
}

var textFile = null;

function makeTextFile(text) {
    var data = new Blob([text], { type: 'text/plain' });

    // If we are replacing a previously generated file we need to
    // manually revoke the object URL to avoid memory leaks.
    if (textFile !== null) {
        window.URL.revokeObjectURL(textFile);
    }

    textFile = window.URL.createObjectURL(data);

    // returns a URL you can use as a href
    return textFile;
}

var App = React.createClass({
    displayName: "App",

    getInitialState: function () {
        return { data: [], start: null, end: null, orientation: "none", tables: [] };
    },
    update: function (state, callback) {
        this.setState(state, callback);
    },
    setOrientation: function (orientation) {
        this.setState({ orientation: orientation });
    },
    handleInput: function (event) {
        this.setState({ rawData: event.target.value });
    },
    import: function (event) {
        var file = event.target.files[0];
        var textType = /text.*/;
        if (file.type.match(textType)) {
            var reader = new FileReader();

            reader.onload = function () {
                var result = Papa.parse(reader.result);
                this.setState({ data: result.data });
            }.bind(this);

            reader.readAsText(file);
        }
    },
    render: function () {
        var or = function (or) {
            return function () {
                this.setOrientation(or);
            }.bind(this);
        }.bind(this);
        return React.createElement(
            "div",
            { className: "full" },
            React.createElement(
                "div",
                { className: "menu" },
                React.createElement(ClearButton, { state: this.state, setState: this.update }),
                Object.keys(Orientation).map(function (key) {
                    return React.createElement(
                        "label",
                        { key: key },
                        React.createElement("input", { type: "radio", value: key, name: "or", onChange: or(key),
                            checked: this.state.orientation == key }),
                        Orientation[key]
                    );
                }.bind(this)),
                React.createElement(SubmitButton, { state: this.state, setState: this.update }),
                React.createElement("br", null),
                React.createElement(
                    "a",
                    { href: makeTextFile(exportTables(this.state.tables)), download: "tables.csv" },
                    "Generate JSON"
                )
            ),
            React.createElement(
                "div",
                { className: "content" },
                React.createElement(Table, { data: this.state.data, state: this.state, setState: this.update }),
                React.createElement("br", null),
                React.createElement("input", { type: "file", onChange: this.import }),
                React.createElement("br", null)
            )
        );
    }
});

var Table = React.createClass({
    displayName: "Table",

    render: function () {
        var i = 1;
        var rows = this.props.data.map(function (row) {
            return React.createElement(Row, { key: i, cells: row, row: i++, state: this.props.state, setState: this.props.setState });
        }.bind(this));
        return React.createElement(
            "table",
            null,
            React.createElement(
                "tbody",
                null,
                rows
            )
        );
    }
});

var Row = React.createClass({
    displayName: "Row",

    render: function () {
        var i = 1;
        var cells = this.props.cells.map(function (cell) {
            return React.createElement(Cell, { key: [this.props.row, i], row: this.props.row, col: i++, content: cell,
                state: this.props.state, setState: this.props.setState });
        }.bind(this));
        return React.createElement(
            "tr",
            null,
            cells
        );
    }
});

var Cell = React.createClass({
    displayName: "Cell",

    isSelected: function () {
        var start = this.props.state.start;
        var end = this.props.state.end;
        if (!start) {
            return false;
        } else if (!end) {
            return this.props.row == start[0] && this.props.col == start[1];
        } else {
            var min = [Math.min(start[0], end[0]), Math.min(start[1], end[1])];
            var max = [Math.max(start[0], end[0]), Math.max(start[1], end[1])];
            return this.props.row >= min[0] && this.props.row <= max[0] && this.props.col >= min[1] && this.props.col <= max[1];
        }
    },
    isDisabled: function () {
        for (var i = 0; i < this.props.state.tables.length; i++) {
            var bounds = this.props.state.tables[i].bounds;
            if (this.props.row >= bounds[0] && this.props.row <= bounds[1] && this.props.col >= bounds[2] && this.props.col <= bounds[3]) {
                return true;
            }
        }
        return false;
    },
    clearState: function () {
        this.props.setState({ start: null, end: null });
    },
    setStart: function (start_r, start_c) {
        this.props.setState({ start: [start_r, start_c] });
    },
    setEnd: function (end_r, end_c) {
        this.props.setState({ end: [end_r, end_c] });
    },
    handleClick: function () {
        if (!this.isDisabled()) {
            if (this.props.state.start) {
                this.setEnd(this.props.row, this.props.col);
            } else {
                this.setStart(this.props.row, this.props.col);
            }
        }
    },
    render: function () {
        var classes = [];
        if (this.isSelected()) {
            classes.push("selected");
        } else if (this.isDisabled()) {
            classes.push("disabled");
        }
        return React.createElement(
            "td",
            { onClick: this.handleClick, className: classes },
            this.props.content
        );
    }
});

var ClearButton = React.createClass({
    displayName: "ClearButton",

    clear: function () {
        this.props.setState({ start: null, end: null });
    },
    render: function () {
        return this.props.state.start ? React.createElement(
            "button",
            { onClick: this.clear },
            "Clear"
        ) : React.createElement(
            "button",
            { disabled: true },
            "Clear"
        );
    }
});

var SubmitButton = React.createClass({
    displayName: "SubmitButton",

    clear: function () {
        this.props.setState({ start: null, end: null, orientation: "none" });
    },
    submit: function () {
        var bounds = [Math.min(this.props.state.start[0], this.props.state.end[0]), Math.max(this.props.state.start[0], this.props.state.end[0]), Math.min(this.props.state.start[1], this.props.state.end[1]), Math.max(this.props.state.start[1], this.props.state.end[1])];
        var table = { bounds: bounds, orientation: this.props.state.orientation };
        this.props.setState({ tables: this.props.state.tables.concat(table) });
        this.clear();
    },
    render: function () {
        var name = "Add table";
        return this.props.state.end ? React.createElement(
            "button",
            { onClick: this.submit },
            name
        ) : React.createElement(
            "button",
            { disabled: true },
            name
        );
    }
});
$(document).ready(function () {
    ReactDOM.render(React.createElement(App, { data: [] }), $("body>div")[0]);
});

//# sourceMappingURL=select-compiled.js.map