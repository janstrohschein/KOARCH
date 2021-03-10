using System;
using System.IO;
using System.Threading.Tasks;
using Avro;
using Avro.Generic;
using Confluent.SchemaRegistry.Serdes;
using Confluent.SchemaRegistry;
using System.Collections.Generic;
using Confluent.Kafka.SyncOverAsync;
using static OPCUAGateway.OPCConnection;
using Confluent.Kafka;
using System.Threading;
using Confluent.Kafka.Admin;

namespace OPCUAGateway
{
    public class KafkaConfig
    {
        public String path_to_schema { get; set; } = @"CPPSdataGeneric.avsc";
        public String bootstrap_servers { get; set; } = "localhost:9092";
        public String schema_registry_url { get; set; } = "http://localhost:8081";
        public String topic_name { get; set; } = "CPPSdata";
        public String groupName { get; set; } = "print_count";
    }
    class Kafka
    {
        /// <summary>
        /// Test function for adaption, whichs sends a message without a schema.
        /// </summary>
        /// <param name="kConfig">Configuration of Kafka</param>
        /// <param name="message">Messeage that should be send, in our Example "Signalname:Value"</param>
        /// <returns></returns>
        public static Object sendMessageWithoutSchema(KafkaConfig kConfig, string message)
        {
            ProducerConfig config = new ProducerConfig{ BootstrapServers = kConfig.bootstrap_servers };
            using (var producer =
                 new ProducerBuilder<Null, string>(config).Build())
            {
                try
                {
                    return producer.ProduceAsync(kConfig.topic_name, new Message<Null, string> { Value = message })
                        .GetAwaiter()
                        .GetResult();
                }
                catch (Exception e)
                {
                    Console.WriteLine($"Oops, something went wrong: {e}");
                }
            }
            return null;
        }
        /// <summary>
        /// Creates a producer that send messages with a certain avro schema.
        /// </summary>
        /// <param name="kConfig">Configuration of the Kafka consumer </param>
        /// <param name="record">Message that will be send</param>
        public static async void sendMessage(KafkaConfig kConfig, GenericRecord record)
        {
            // Producer configuration, make sure port and ip work, set also do ipv4 to avoid ipv6 errors
            var config = new Confluent.Kafka.ProducerConfig
            {
                BootstrapServers = kConfig.bootstrap_servers,
                BrokerAddressFamily = Confluent.Kafka.BrokerAddressFamily.V4,
            };

            // Producer schema configuration, make sure kafka provides a schema url
            var schema = new Confluent.SchemaRegistry.SchemaRegistryConfig
            {
                Url = kConfig.schema_registry_url
            };

            // Setting up the producer with the schema
            using (var schemaRegistry = new CachedSchemaRegistryClient(schema))
            using (var producer = new Confluent.Kafka.ProducerBuilder<Confluent.Kafka.Null, GenericRecord>(config)
                    .SetValueSerializer(new AvroSerializer<GenericRecord>(schemaRegistry))
                    .Build())
            {
                // Try to produce a message
                try
                {
                    var dr = await producer
                    .ProduceAsync(kConfig.topic_name, new Confluent.Kafka.Message<Confluent.Kafka.Null, GenericRecord> { Value = record });
                    Console.WriteLine("Produced to: {0}", dr.TopicPartitionOffset);
                }
                catch (Confluent.Kafka.ProduceException<Confluent.Kafka.Null, GenericRecord> ex)
                {
                    Console.WriteLine(ex);
                }
                // Delete the queue 
                producer.Flush();
            }
        }

        /// <summary>
        /// Creates a consumer that listen to a certain topic and use the content to adapt the OPC UA server that is specified by the parameters of this method.
        /// </summary>
        /// <param name="kConfig">Configuration of the Kafka consumer</param>
        /// <param name="adaptionConfig">Configuration of the OPC UA Server, where updates arriving by kafka messages are provided to</param>
        public static void RunConsumerWithoutSchema(KafkaConfig kConfig, OPC adaptionConfig)
        {
            CheckTopicAvailability(kConfig.bootstrap_servers, kConfig.topic_name);
            // Consumer configuration, make sure port and ip work, set also do ipv4 to avoid ipv6 errors
            var config = new Confluent.Kafka.ConsumerConfig
            {
                BootstrapServers = kConfig.bootstrap_servers,
                BrokerAddressFamily = Confluent.Kafka.BrokerAddressFamily.V4,
                GroupId = kConfig.groupName,
                AutoOffsetReset = AutoOffsetReset.Earliest
            };
            var consumeTask = Task.Run(() =>
            {
                using (var builder = new ConsumerBuilder<Ignore,
                string>(config).Build())
                {
                    builder.Subscribe(kConfig.topic_name);
                    var cancelToken = new CancellationTokenSource();
                    try
                    {
                        while (true)
                        {
                            var consumer = builder.Consume(cancelToken.Token);
                            Console.WriteLine($"Message: {consumer.Message.Value} received from {consumer.TopicPartitionOffset}");
                            String[] signals = consumer.Message.Value.Split(":");
                            adaptOPC(adaptionConfig, signals);
                        }
                    }
                    catch (Exception e)
                    {
                        Console.Error.WriteLine("Consumer Error: " + e);
                        builder.Close();
                    }
                }
            });
        }

        /// <summary>
        /// Method checks, if the topic is availabe at the bootstrap server and in not the topic is created to prevent an error at the first occurence
        /// </summary>
        /// <param name="bootstrapServers">Adress of the bootstrap server</param>
        /// <param name="topicName">Name of the topic that should be checked</param>
        static async void CheckTopicAvailability(string bootstrapServers, string topicName)
        {
            using (var adminClient = new AdminClientBuilder(new AdminClientConfig { BootstrapServers = bootstrapServers }).Build())
            {
                Boolean topicExists = false;
                try
                {
                    Metadata md = adminClient.GetMetadata(topicName, new TimeSpan(0, 0, 1, 0));
                    List<TopicMetadata> topics = md.Topics;
                    for (int i = 0; i < topics.Count; i++)
                    {
                        if (topics[i].Topic.Equals(topicName))
                        {
                            topicExists = true;
                        }
                    }
                }
                catch(Exception e)
                {
                    Console.Error.WriteLine(e);
                }
                if (!topicExists) { 
                try
                {
                    await adminClient.CreateTopicsAsync(new TopicSpecification[] {
                        new TopicSpecification { Name = topicName, ReplicationFactor = 1, NumPartitions = 1 } });
                }
                catch (CreateTopicsException e)
                {
                    Console.WriteLine($"An error occured creating topic {e.Results[0].Topic}: {e.Results[0].Error.Reason}");
                }
            }
            }
        }
    }
}


