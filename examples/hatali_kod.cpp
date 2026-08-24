#include <iostream>
#include <cstdio>
#include <cstring>
#include <cstdlib>

// --- HATA 1: Hard-coded C++ Credentials ---
const char* API_KEY = "sk-cpp9876543210secretkey";
#define DB_PASSWORD "SuperSecretCppPass123!"

void process_input(const char* user_input) {
    char buffer[64];

    // --- HATA 2: Unsafe strcpy (Buffer Overflow) ---
    strcpy(buffer, user_input);

    // --- HATA 3: Format String Açığı ---
    printf(buffer);

    // --- HATA 4: system() Kabuk Enjeksiyonu ---
    char cmd[128];
    sprintf(cmd, "echo User input: %s", user_input);
    system(cmd);
}

void memory_leak_example() {
    // --- HATA 5: malloc without NULL check & Memory Leak ---
    char* data = (char*)malloc(1024);
    strcpy(data, "Dinamik bellek tahsisi yapildi fakat free edilmedi.");
    std::cout << data << std::endl;
    // free(data); unutuldu!
}

int main(int argc, char* argv[]) {
    if (argc > 1) {
        process_input(argv[1]);
    }
    memory_leak_example();
    return 0;
}
