// Örnek hatalı JS dosyası
function processUserData(userInput) {
    document.getElementById("output").innerHTML = "<div>" + userInput + "</div>";
    document.write("Loading data...");
    
    var token = "secret_api_token_123456789";
    localStorage.setItem("auth_token", token);
    
    console.log("User password logged:", userInput);
}
