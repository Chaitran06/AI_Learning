#include <iostream>
#include <string>
#include <vector>

using namespace std;

int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

int multiply(int a, int b) {
    return a * b;
}

double divide(int a, int b) {
    if (b == 0) {
        cout << "Error: division by zero" << endl;
        return 0;
    }
    return (double)a / b;
}

long long factorial(int n) {
    long long result = 1;
    for (int i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

bool isPrime(int n) {
    if (n < 2) {
        return false;
    }
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) {
            return false;
        }
    }
    return true;
}

int findMax(const vector<int>& nums) {
    int maxVal = nums[0];
    for (size_t i = 1; i < nums.size(); i++) {
        if (nums[i] > maxVal) {
            maxVal = nums[i];
        }
    }
    return maxVal;
}

string reverseString(const string& s) {
    string reversed = "";
    for (int i = s.size() - 1; i >= 0; i--) {
        reversed += s[i];
    }
    return reversed;
}

int main() {
    cout << "add(5, 3) = " << add(5, 3) << endl;
    cout << "subtract(10, 4) = " << subtract(10, 4) << endl;
    cout << "multiply(6, 7) = " << multiply(6, 7) << endl;
    cout << "divide(9, 2) = " << divide(9, 2) << endl;
    cout << "factorial(5) = " << factorial(5) << endl;
    cout << "isPrime(17) = " << (isPrime(17) ? "true" : "false") << endl;

    vector<int> nums = {3, 9, 2, 7, 5};
    cout << "findMax({3, 9, 2, 7, 5}) = " << findMax(nums) << endl;

    cout << "reverseString(\"hello\") = " << reverseString("hello") << endl;
    return 0;
}
