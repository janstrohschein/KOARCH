var app = require('express')();
var http = require('http');
var server = http.createServer(app);
var io = require('socket.io')(server);
var myParser = require('body-parser');

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
		
		jsonMessage = JSON.stringify(decodedMessage);
  
		const options = {
			hostname: '3_API_Plot',
			port: 8000,
			path: '/postData',
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Content-Length': Buffer.byteLength(jsonMessage)
			}
		}
		
		const req = http.request(options, res => {
			res.setEncoding('utf8');
			console.log(`statusCode: ${res.statusCode}`)
			
			res.on('data', d => {
				process.stdout.write(d)
			})
		})
		
		req.on('error', error => {
			console.error(error)
		})
		
		req.write(jsonMessage)
		req.end()

		io.emit("refresh", decodedMessage.source);
	})
});

app.use(myParser.urlencoded({extended: true}));

app.get('/plotData', (req, res) => {
	
	var options = {
		hostname: '3_API_Plot',
		port: 8000,
		path: '/getData'
	  };
	  
	  callback = function(response) {
		response.setEncoding('utf8');
		var str = '';
	  
		//another chunk of data has been received, so append it to `str`
		response.on('data', function (chunk) {
		  str += chunk;
		});
	  
		//the whole response has been received, so we just print it out here
		response.on('end', function () {
		  res.send(str);
		});
	  }
	  
	  http.request(options, callback).end();
});

app.get('/plotMultipleData', (req, res) => {

	var options = {
		hostname: '3_API_Plot',
		port: 8000,
		path: '/getDataMultiple'
	  };
	  
	  callback = function(response) {
		response.setEncoding('utf8');
		var str = '';
	  
		//another chunk of data has been received, so append it to `str`
		response.on('data', function (chunk) {
		  str += chunk;
		});
	  
		//the whole response has been received, so we just print it out here
		response.on('end', function () {
		  res.send(str);
		});
	  }
	  
	  http.request(options, callback).end();
});

server.listen(8000);

//Message
console.log("Server running at http://127.0.0.1:8003/");
