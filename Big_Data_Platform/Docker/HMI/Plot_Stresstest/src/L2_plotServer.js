var app = require('express')();
var http = require('http').createServer(app);
var io = require('socket.io')(http);
var myParser = require('body-parser');
var avro = require('avsc');

const {spawn} = require('child_process');
const avroSchemaRegistry = require('avro-schema-registry');

const schemaRegistry = 'http://schema-registry:8081';
const registry = avroSchemaRegistry(schemaRegistry);

var data = {};
var dataMultiple = {};

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
	registry.decode(message.value).then((decodedMessage) => {

		if (decodedMessage.x_int_to_date) {
			var temp = new Date(decodedMessage.x_data * 1000);
			decodedMessage.x_data = temp.toISOString().split('T')[0] + ' ' + temp.toTimeString().split(' ')[0];
		}

		delete decodedMessage.x_int_to_date;
		delete decodedMessage.plot;

		if (decodedMessage.multi_filter != null) {
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
	})
});

app.use(myParser.urlencoded({extended: true}));

app.get('/plotData', (req, res) => {
	
	var dataToSend = '';
	// change the last parameter to name of given xaxis key
	const python = spawn('python', ['L2_plotData.py', 'singleData']);
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
	const python = spawn('python', ['L2_plotData.py', 'multiData']);
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

app.get('/singleData', (req, res) => {

	res.send(data);

});

app.get('/multiData', (req, res) => {


	res.send(dataMultiple);

});



http.listen(8000);

//Message
console.log("Server running at http://127.0.0.1:8003/");
