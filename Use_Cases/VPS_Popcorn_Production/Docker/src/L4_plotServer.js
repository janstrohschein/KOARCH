var app = require('express')();
var http = require('http').createServer(app);
var io = require('socket.io')(http);
var myParser = require('body-parser');
var avro = require('avsc');

const {spawn} = require('child_process');
const fs = require('fs');
const { decode } = require('punycode');

const importedSchema = fs.readFileSync('./schema/plot.avsc', 'utf8');


var data = {};
var dataMultiple = {};

const type = avro.Type.forSchema(JSON.parse(importedSchema));

var kafka = require('kafka-node'),

	client = new kafka.KafkaClient({kafkaHost: 'kafka:9093'}),
	options = {
		kafkaHost: 'kafka:9093',
		autoCommit: false,
		fromOffset: 'earliest',
		commitOffsetsOnFirstJoin: false,
		encoding: 'buffer'
	}
	consumer = new kafka.ConsumerGroup(options, 'AB_plot_data');

client.on('ready', function(){
		console.log('Client ready!');
});

consumer.on('error', function (err) {
	console.log("Kafka Error: Consumer - " + err);
});

consumer.on('message', function (message) {
	console.log("Message received");
	var decodedMessage = type.fromBuffer(message.value);

	if (decodedMessage.x_int_to_date) {
		var temp = new Date(decodedMessage.x_data * 1000);
		decodedMessage.x_data = temp.toISOString().split('T')[0] + ' ' + temp.toTimeString().split(' ')[0];
	}

	delete decodedMessage.x_int_to_date;
	delete decodedMessage.plot;

	if (decodedMessage.multiplefilter != null) {
		if (!(decodedMessage.source in dataMultiple)) {
			dataMultiple[decodedMessage.source] = [];
		}
		dataMultiple[decodedMessage.source].push(decodedMessage);
	}
	else {
		if (!(decodedMessage.source in data)) {
			data[decodedMessage.source] = [];
		}
		data[decodedMessage.source].push(decodedMessage);
	}

	delete decodedMessage.source;

	io.emit("refresh");
});

app.use(myParser.urlencoded({extended: true}));

app.get('/plotData', (req, res) => {
	
	var dataToSend = '';
	// change the last parameter to name of given xaxis key
	const python = spawn('python', ['L4_plotData.py', JSON.stringify(data)]);
	python.stdout.on('data', function(data) {
		dataToSend += data.toString();
	});

	python.on('close', (code) => {
		console.log(`child process close all stdio with code ${code}`);
		res.send(dataToSend);
	})

	python.stderr.on('data', function(err) {
		console.log(err.toString());
	});
});

app.get('/plotMultipleData', (req, res) => {

	var dataToSend = '';
	// change 3rd parameter to name of given xaxiskey nad 4th parameter to key of user
	const python = spawn('python', ['L4_plotData.py', JSON.stringify(dataMultiple)]);
	python.stdout.on('data', function(data) {
		dataToSend += data.toString();
	});

	python.on('close', (code) => {
		console.log(`child process close all stdio with code ${code}`);
		res.send(dataToSend);
	})

	python.stderr.on('data', function(err) {
		console.log(err.toString());
	});
});

http.listen(8000);

//Message
console.log("Server running at http://127.0.0.1:8000/");
