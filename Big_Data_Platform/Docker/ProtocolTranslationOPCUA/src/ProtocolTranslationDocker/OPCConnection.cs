using System;
using System.Collections.ObjectModel;
using System.Threading;
using LibUA.Core;
using static LibUA.Program;

namespace OPCUAGateway
{
    class OPCConnection
    {
        public class OPC
        {
            public String opcServer { get; set; }
            public OPCConfig opcConfig { get; set; }
        }
        public class OPCConfig
        {
            public Collection<String> node { get; set; }
            public int interval { get; set; }
        }
        public class Nodes
        {
            public Collection<String> node { get; set; }
        }

        public static LibUA.Client client;
        /// <summary>
        /// Connects to the OPC Server that is speficied by the url, and request the node from the server spcified by nodes. This happend 10 times, for demonstration purposes.
        /// This method detemines the data type and provide the information to the output. All typical data types are supported except FLOAT.
        /// The interval parameter is not used coorrectly, since it is implemented as a sleep of the thread, so not the OPC functionallity is used
        /// </summary>
        /// <param name="url">Complete address of the OPC Server</param>
        /// <param name="nodes">Nodes of the server that should be queried</param>
        /// <param name="interval"> interval in milliseconds, how long the time span between two queries should be</param>
        /// <returns> Two dimensional String array, size: [nodes.Count(), 3]. With signal name in [,0], data type in [,1] and value (converted to string) in [,2]</returns>
        public static Object[,] readFromOPC(String url, Collection<String> nodes, int interval)
        {
            Thread.Sleep(interval);
            Object[,] value = new Object[nodes.Count, 2];
            if ((client == null) || !client.IsConnected)
            {
                client = OPCConnectToServer(url);
            }
            Object[] opcValues = OPCReadNotes(client, nodes);
            for (int i = 0; i < nodes.Count; i++)
            {
                value[i, 0] = nodes[i];
                value[i, 1] = ((LibUA.Core.DataValue)opcValues[i]).Value;
                Console.WriteLine("Node: " + nodes[i] + " has the value " + value[i, 1] + ".");
            }


            return value;
        }

        /// <summary>
        /// Connects to the OPC UA server specified the the URL and write a value to the note. The type of the note is requested first and the value is casted to that type.
        /// </summary>
        /// <param name="url">URL of the OPC UA Server</param>
        /// <param name="nodes">Notes that should be adpated</param>
        /// <param name="values">New values of the node</param>
        /// <returns></returns>
        public static Boolean writeSingleValueToOPC(String url, String nodes, Object values)
        {
            if ((client == null) || !client.IsConnected)
            {
                client = OPCConnectToServer(url);
            }
                DataValue[] dt = null;
                var readRes = client.Read(new ReadValueId[]
                    {
                    new ReadValueId(new NodeId(4, nodes), NodeAttribute.DataType, null, new QualifiedName(0, null)),
                    }, out dt);
            LibUA.Core.NodeId datatype = (LibUA.Core.NodeId)dt[0].Value;
            Console.WriteLine("Will write value to OPC UA: " + nodes);
            try
            {
                uint[] respStatuses;
                switch (datatype.NumericIdentifier)
                {
                    case (uint)LibUA.Core.VariantType.UInt32:
                        client.Write(new WriteValue[]{new WriteValue(new NodeId(4, nodes), NodeAttribute.Value, null,
                        new DataValue(UInt32.Parse((String)values)))}, out respStatuses);
                        Console.WriteLine("For Node " + nodes + " set value to " + values);
                        break;
                    case (uint)LibUA.Core.VariantType.Boolean:
                        client.Write(new WriteValue[]{new WriteValue(new NodeId(4, nodes), NodeAttribute.Value, null,
                        new DataValue(Boolean.Parse((String)values)))}, out respStatuses);
                        Console.WriteLine("For Node " + nodes + " set value to " + values);
                        break;
                    case (uint)LibUA.Core.VariantType.String:
                        client.Write(new WriteValue[]{new WriteValue(new NodeId(4, nodes), NodeAttribute.Value, null,
                        new DataValue((String)values))}, out respStatuses);
                        Console.WriteLine("For Node " + nodes + " set value to " + values);
                        break;
                    case (uint)LibUA.Core.VariantType.Int32:
                        client.Write(new WriteValue[]{new WriteValue(new NodeId(4, nodes), NodeAttribute.Value, null,
                        new DataValue(Int32.Parse((String)values)))}, out respStatuses);
                        Console.WriteLine("For Node " + nodes + " set value to " + values);
                        break;
                    case (uint)LibUA.Core.VariantType.Double:
                        client.Write(new WriteValue[]{new WriteValue(new NodeId(4, nodes), NodeAttribute.Value, null,
                        new DataValue(Double.Parse((String)values)))}, out respStatuses);
                        Console.WriteLine("For Node " + nodes + " set value to " + values);
                        break;
                    case (uint)LibUA.Core.VariantType.Float:
                        client.Write(new WriteValue[]{new WriteValue(new NodeId(4, nodes), NodeAttribute.Value, null,
                        new DataValue(float.Parse((String)values)))}, out respStatuses);
                        Console.WriteLine("For Node " + nodes + " set value to " + values);
                        break;
                    default:
                            Console.WriteLine("Error: Could not find data type (" + dt[0].ToString() + ") of: " + nodes);
                        break;
                }
            }
            catch (Exception e)
            {
                Console.Error.WriteLine("OPC error: " + e);
            }
            return true;
        }

        /// <summary>
        /// Testfunction - Provide information for OPC UA connection for adaption. This is an auxillary function that is only used for test purpose and can be replaced later on.
        /// </summary>
        /// <returns>Data of the type OPC that is defined above.</returns>
        public static OPC opcAdaption(Boolean docker)
        {
            String opcAdress = "";
            if (docker)
            {
                opcAdress = @"opc.tcp://docker.for.win.localhost:48020";
            }
            else
            {
                opcAdress = @"opc.tcp://localhost:48020";
            }
            Collection<String> tmp = new Collection<string>();
            tmp.Add("Demo.SimulationActive");
            tmp.Add("Demo.SimulationSpeed");

            var opcdata = new OPC
            {
                opcServer = opcAdress,
                opcConfig = new OPCConfig
                {
                    node = tmp,
                    interval = 100,
                }
            };
            return opcdata;
        }
        
        /// <summary>
        /// Testmethod to write values to an OPC UA server
        /// </summary>
        /// <param name="config">Config of the OPC UA Server</param>
        /// <param name="signals">Signal names and values that should be updated at the server</param>
        public static void adaptOPC(OPC config, String[] signals)
        {
            try
            {
                writeSingleValueToOPC(config.opcServer, signals[0], signals[1]);
            }
            catch
            {
                Console.Error.WriteLine("Error: Could not write values to OPC Server " + config.opcServer);
            }
        }
        
    }
}
