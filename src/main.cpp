#include <iostream>
#include "calculator.h"

int main() {
    Calculator calc;
    
    std::cout << "=== Simple Calculator ===" << std::endl;
    std::cout << "5 + 3 = " << calc.add(5, 3) << std::endl;
    std::cout << "10 - 4 = " << calc.subtract(10, 4) << std::endl;
    std::cout << "6 * 7 = " << calc.multiply(6, 7) << std::endl;
    std::cout << "20 / 4 = " << calc.divide(20, 4) << std::endl;
    std::cout << "10 / 0 = " << calc.divide(10, 0) << " (expected: 0)" << std::endl;
    
    // 故意引入编译错误：调用一个不存在的函数
    
    return 0;
}