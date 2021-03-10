using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using LibUA.Core;


//This KOARCH client is an adapted version to the KOARCH project of the example of nauful from https://github.com/nauful/LibUA


namespace LibUA
{
    public class Program
    {
        class KOARCHClient : Client
        {

            X509Certificate2 appCertificate = null;
            RSACryptoServiceProvider cryptPrivateKey = null;

            public override X509Certificate2 ApplicationCertificate
            {
                get { return appCertificate; }
            }

            public override RSACryptoServiceProvider ApplicationPrivateKey
            {
                get { return cryptPrivateKey; }
            }

            private void LoadCertificateAndPrivateKey()
            {
                try
                {
                    // Try to load existing (public key) and associated private key
                    appCertificate = new X509Certificate2("ClientCert.der");
                    cryptPrivateKey = new RSACryptoServiceProvider();

                    var rsaPrivParams = UASecurity.ImportRSAPrivateKey(File.ReadAllText("ClientKey.pem"));
                    cryptPrivateKey.ImportParameters(rsaPrivParams);
                }
                catch
                {
                    // Make a new certificate (public key) and associated private key
                    var dn = new X500DistinguishedName("CN=Client certificate;OU=Demo organization",
                        X500DistinguishedNameFlags.UseSemicolons);
                    SubjectAlternativeNameBuilder sanBuilder = new SubjectAlternativeNameBuilder();
                    sanBuilder.AddUri(new Uri("urn:DemoApplication"));

                    using (RSA rsa = RSA.Create(2048))
                    {
                        var request = new CertificateRequest(dn, rsa, HashAlgorithmName.SHA256,
                            RSASignaturePadding.Pkcs1);

                        request.CertificateExtensions.Add(sanBuilder.Build());

                        var certificate = request.CreateSelfSigned(new DateTimeOffset(DateTime.UtcNow.AddDays(-1)),
                            new DateTimeOffset(DateTime.UtcNow.AddDays(3650)));

                        appCertificate = new X509Certificate2(certificate.Export(X509ContentType.Pfx, ""),
                            "", X509KeyStorageFlags.DefaultKeySet);

                        var certPrivateParams = rsa.ExportParameters(true);
                        File.WriteAllText("ClientCert.der", UASecurity.ExportPEM(appCertificate));
                        File.WriteAllText("ClientKey.pem", UASecurity.ExportRSAPrivateKey(certPrivateParams));

                        cryptPrivateKey = new RSACryptoServiceProvider();
                        cryptPrivateKey.ImportParameters(certPrivateParams);
                    }
                }
            }

            public KOARCHClient(string Target, int Port, int Timeout)
                : base(Target, Port, Timeout)
            {
                LoadCertificateAndPrivateKey();
            }

            public override void NotifyDataChangeNotifications(uint subscrId, uint[] clientHandles, DataValue[] notifications)
            {
                for (int i = 0; i < clientHandles.Length; i++)
                {
                    Console.WriteLine("subscrId {0} handle {1}: {2}", subscrId, clientHandles[i], notifications[i].Value.ToString());
                }
            }

            public override void NotifyEventNotifications(uint subscrId, uint[] clientHandles, object[][] notifications)
            {
                for (int i = 0; i < clientHandles.Length; i++)
                {
                    Console.WriteLine("subscrId {0} handle {1}: {2}", subscrId, clientHandles[i], string.Join(",", notifications[i]));
                }
            }
        }

        static ApplicationDescription[] appDescs = null;
        static EndpointDescription[] endpointDescs = null;
        static Boolean initilized = false;
        public static LibUA.Client OPCConnectToServer(String url)
        {
            Console.WriteLine("OPC UA URL: " + url);
            LibUA.Client client = null;
            if (url.Contains("opc.tcp://"))
            {
                url = url.Replace("opc.tcp://", "");
            }
            String[] ip = url.Split(":");
            if (!initilized)
            {
                Console.WriteLine("Connecting");
                client = new KOARCHClient(ip[0], int.Parse(ip[1]), 1000);
                client.Connect();
                Console.WriteLine("OPC UA is connected: " + client.IsConnected);
                client.OpenSecureChannel(MessageSecurityMode.None, SecurityPolicy.None, null);
                client.FindServers(out appDescs, new[] { "en" });
                client.GetEndpoints(out endpointDescs, new[] { "en" });
                client.Disconnect();
                initilized = true;
            }

            var appDesc = new ApplicationDescription(
            "urn:KORCHDemoApplication", "uri:KOARCHDemoApplication", new LocalizedText("OPC UA Client"),
            ApplicationType.Client, null, null, null);

            var connectRes = client.Connect();
            var openRes = client.OpenSecureChannel(MessageSecurityMode.None, SecurityPolicy.None, null);
            var createRes = client.CreateSession(appDesc, "urn:DemoApplication", 120);
            var activateRes = client.ActivateSession(new UserIdentityAnonymousToken("0"), new[] { "en" });
            return client;
        }

        public static Object[] OPCReadNotes(LibUA.Client client, Collection<String> nodes)
        {
            DataValue[] dvs = null;
            ReadValueId[] node = new ReadValueId[nodes.Count];
            for (int i = 0; i < node.Length; i++)
            {
                node[i] = new ReadValueId(new NodeId(4, nodes[i]), NodeAttribute.Value, null, new QualifiedName(0, null));
            }
            var readRes = client.Read(node, out dvs);

            return dvs;
        }

        public static void OPCSubscribe(LibUA.Client client, Collection<String> nodes)
        {
            uint subscrId;
            client.CreateSubscription(50, 1000, true, 0, out subscrId);
            uint clientHandleEventMonitor = 0;

            MonitoredItemCreateRequest[] monitor = new MonitoredItemCreateRequest[nodes.Count];
            ReadValueId[] node = new ReadValueId[nodes.Count];
            for (int i = 0; i < node.Length; i++)
            {
                node[i] = new ReadValueId(new NodeId(4, nodes[i]), NodeAttribute.Value, null, new QualifiedName(0, null));
                monitor[i] = new MonitoredItemCreateRequest(node[i], MonitoringMode.Reporting, new MonitoringParameters(clientHandleEventMonitor, 100, null, 100, true));
            }

            MonitoredItemCreateResult[] monitorCreateResults;
            client.CreateMonitoredItems(subscrId, TimestampsToReturn.Both, monitor, out monitorCreateResults);


            Console.WriteLine("Start Monitoring Items");
            Console.ReadKey();

            client.Dispose();
            Console.WriteLine("is connected: " + client.IsConnected);
        }
    }
}
