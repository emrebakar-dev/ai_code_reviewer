using System;
using System.Data.SqlClient;
using System.Diagnostics;
using System.IO;
using System.Runtime.Serialization.Formatters.Binary;

namespace LogAnalyzerExample
{
    public class LogAnalyzer
    {
        private string apiKey = "secret_api_key_998877665544";

        public void ProcessLogs(string logLevel, string userInput)
        {
            // 1. SQL Injection Risk
            string query = "SELECT * FROM Logs WHERE Level = '" + logLevel + "'";
            SqlCommand cmd = new SqlCommand(query);

            // 2. Command Injection Risk
            Process.Start("cmd.exe", "/c echo " + userInput);

            // 3. Unsafe Deserialization
            BinaryFormatter formatter = new BinaryFormatter();
            MemoryStream stream = new MemoryStream();
            object obj = formatter.Deserialize(stream);

            // 4. Resource Leak
            StreamReader reader = new StreamReader("log.txt");
            string content = reader.ReadToEnd();

            // 5. Empty Catch
            try
            {
                int val = int.Parse(userInput);
            }
            catch (Exception)
            {
            }
        }
    }
}
