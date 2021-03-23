using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;
using static OPCUAGateway.OPCConnection;
using OPCUAGateway;
using Avro.Generic;
using Avro;

namespace KafkaSchema.OPCUAGateway
{
    class Program
    {
        //Variable to enable an easy switching to a local system to enable debugging
        static Boolean docker = true;
        static void Main(string[] args)
        {

            String path = "";
            if (!docker)
            {
                path = @"/config.yml"; //adapt to your local path
            }
            else
            {
                path = "/app/src/config/config.yml";
            }

            //Create config for OPC and Kafka for OPC to Kafka
            OPC readData = readYamlFromFile(path);
            KafkaConfig prodConfig = GetKafkaProducerConfig(new KafkaConfig(), "CPPSdata");

            //Create config for OPC and Kafka for Kafka to OPC
            OPC opcAdpation = opcAdaption(docker);
            KafkaConfig consConfig = GetKafkaConsumerConfig(new KafkaConfig(), "CPPSadaption", "CPPSadaption");

            //Create Consumer for the adaption; due to implementation issues without a schema
            Kafka.RunConsumerWithoutSchema(consConfig, opcAdpation);

            // Read values from OPC and send to Kafka
            for (int i = 0; i < 10; i++)
            {
                Object[,] values = readFromOPC(readData.opcServer, readData.opcConfig.node, readData.opcConfig.interval);
                Kafka.sendMessage(prodConfig, createMessageForCPPSdataGeneric(prodConfig, values));
            }

            //Function to send a message that results in an adaption of a signal
            sendTestToAdaption();

            Console.ReadLine();
        }

        /// <summary>
        /// This is a test method to check whether or not the adaption on OPC Server works fine
        /// </summary>
        public static void sendTestToAdaption()
        {
            List<Object> adpationValues = new List<object>();
            adpationValues.Add(true);
            KafkaConfig prodAdaptConfig = new KafkaConfig();
            prodAdaptConfig.topic_name = "CPPSadaption";
            if (docker)
            {
                prodAdaptConfig.bootstrap_servers = @"kafka:9093";
            }
            Object tmp = Kafka.sendMessageWithoutSchema(prodAdaptConfig, "Demo.SimulationSpeed:20");
        }

        /// <summary>
        /// Creates a message with the provided data for a certain Kafka config with the CPPSdataGeneric Schema
        /// </summary>
        /// <param name="kConfig">Config of the kafka config - only the path to the schema is relevant </param>
        /// <param name="data">Two dimensional array with signal name in the first column and the value in the second </param>
        /// <returns></returns>
        public static GenericRecord createMessageForCPPSdataGeneric(KafkaConfig kConfig, Object[,] data)
        {
            // Defines a record for the used schema
            RecordSchema s = (RecordSchema)RecordSchema.Parse(File.ReadAllText(kConfig.path_to_schema));
            var record = new GenericRecord(s);
            IDictionary<String, object> signals = new Dictionary<String, object>();
            for (int i = 0; i < data.GetLength(0); i++)
            {
                signals.Add((String)data[i, 0], data[i, 1]);
            }
            record.Add("Signals", signals);
            return record;
        }

        public static KafkaConfig GetKafkaProducerConfig(KafkaConfig prodConfig, String topicName)
        {
            if (!docker)
            {
                prodConfig.path_to_schema = @"/CPPSdataGeneric.avsc"; //adapt to your local path
                prodConfig.schema_registry_url = @"http://localhost:8081";
                prodConfig.bootstrap_servers = @"localhost:9092";
            }
            else
            {
                prodConfig.path_to_schema = @"/app/src/schema/CPPSdataGeneric.avsc";
                prodConfig.schema_registry_url = @"http://schema-registry:8081";
                prodConfig.bootstrap_servers = @"kafka:9093";
            }
            prodConfig.topic_name = topicName;
            return prodConfig;
        }

        public static KafkaConfig GetKafkaConsumerConfig(KafkaConfig consConfig, String topicName, String groupName)
        {
            if (!docker)
            {
                consConfig.bootstrap_servers = @"localhost:9092";
                consConfig.schema_registry_url = @"http://localhost:8081";
                consConfig.path_to_schema = @"/CPPSadaption.avsc"; //adapt to your local path
            }
            else
            {
                consConfig.path_to_schema = @"/app/src/schema/CPPSadaption1.avsc";
                consConfig.schema_registry_url = @"http://schema-registry:8081";
                consConfig.bootstrap_servers = @"kafka:9093";
            }
            consConfig.topic_name = topicName;
            consConfig.groupName = groupName;
            return consConfig;
        }
/// <summary>
/// Creates a message for the CPPS adaption - only needed for testing
/// </summary>
/// <param name="kConfig">Config of the kafka config - only the path to the schema is relevant </param>
/// <returns></returns>
public static GenericRecord createMessageForCPPSadaption(KafkaConfig kConfig)
        {
            RecordSchema s = (RecordSchema)RecordSchema.Parse(File.ReadAllText(kConfig.path_to_schema));
            // Defines a record for the used schema
            var record = new GenericRecord(s);

            record.Add("SimulationSpeed", 20);
            return record;
        }

        /// <summary>
        /// Read information of the type OPC from a YAML file which is specified by the path
        /// </summary>
        /// <param name="path"> Speficies whoch yml file should be read</param>
        /// <returns> Variable of the type OPC which is defined above</returns>
        public static OPC readYamlFromFile(String path)
        {
            String yml = File.ReadAllText(path);

            var deserializer = new DeserializerBuilder()
            .WithNamingConvention(CamelCaseNamingConvention.Instance)  // UnderscoredNamingConvention: see height_in_inches in sample yml Alternativly: CamelCaseNamingConvention
            .Build();
            Dictionary<object, object> p = (Dictionary<object, object>)deserializer.Deserialize<Object>(yml);
            // determine the relevant section
            Object wantedSection = new Object();
            for (int i = 0; i < p.Count; i++)
            {
                if (("0p_opc").Equals((string)p.ElementAt(i).Key))
                {
                    wantedSection = p.ElementAt(i).Value;
                    break;
                }
            }
            // use the Serializer and Deserialize to convert the data type from Object to OPC
            var serializer = new YamlDotNet.Serialization.Serializer();
            OPC opc = deserializer.Deserialize<OPC>(serializer.Serialize(wantedSection));
            return opc;
        }
    }
}
