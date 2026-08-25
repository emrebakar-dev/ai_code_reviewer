import java.sql.Connection;
import java.sql.Statement;
import java.io.*;
import java.util.List;
import java.util.ArrayList;

public class HataliKod {

    private static final String API_KEY = "supersecretkey123";
    private static String password = "admin1234";

    public static void main(String[] args) throws Exception {

        String username = args.length > 0 ? args[0] : "admin";
        Connection conn = null;
        Statement stmt = conn.createStatement();
        String query = "SELECT * FROM users WHERE name = '" + username + "'";
        stmt.execute(query);

        Runtime.getRuntime().exec("ls " + username);

        System.out.println("Kullanici sifresi: " + password);
        System.out.println("API key: " + API_KEY);

        String role = "admin";
        if (role == "admin") {
            System.out.println("Admin giris yapti");
        }

        try {
            int result = 10 / 0;
        } catch (Exception e) {}

        ObjectInputStream ois = new ObjectInputStream(new FileInputStream("data.ser"));
        Object obj = ois.readObject();
        ois.close();

        try {
            riskyOperation();
        } catch (Exception e) {
            e.printStackTrace();
        }

        List rawList = new ArrayList();
        rawList.add("test");
        rawList.add(42);
    }

    public static void riskyOperation() throws Exception {
        ProcessBuilder pb = new ProcessBuilder("bash", "-c", "whoami");
        pb.start();
    }
}
