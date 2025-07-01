from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def make_sound(self):
        pass

class Dog(Animal):
    def make_sound(self):
        print("Woof")
        
class Cat(Animal):
    def make_sound(self):
        print("Meow")
        
