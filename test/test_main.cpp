#include <cstdio>

// Test framework - minimal
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

void test_assert(bool condition, const char* name) {
    tests_run++;
    if (condition) {
        tests_passed++;
        printf("  PASS: %s\n", name);
    } else {
        tests_failed++;
        printf("  FAIL: %s\n", name);
    }
}

// Defined in test files
void test_memory();
void test_web3();
void test_container();

int main() {
    printf("=== Solarpunk Computing Tests ===\n\n");

    printf("[Memory Manager]\n");
    test_memory();

    printf("\n[Web3 / Keccak-256]\n");
    test_web3();

    printf("\n[Container Runtime]\n");
    test_container();

    printf("\n=== Results: %d/%d passed", tests_passed, tests_run);
    if (tests_failed > 0) {
        printf(" (%d FAILED)", tests_failed);
    }
    printf(" ===\n");

    return tests_failed > 0 ? 1 : 0;
}
