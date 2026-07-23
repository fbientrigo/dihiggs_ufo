#include "Pythia8/Pythia.h"

#include <iostream>

int main() {
  Pythia8::Pythia pythia;
  if (!pythia.readString("Next:numberShowInfo = 0")) return 1;
  std::cout << "Pythia link probe passed\n";
  return 0;
}
