class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email
        
    def validate(self):
        """Validate user data"""
        return len(self.username) > 0 and '@' in self.email
        
    def save(self):
        """Save user to database"""
        from database import save_to_db
        save_to_db(self)
        
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price
        
    def discount(self, percent):
        """Apply discount to product"""
        self.price = self.price * (1 - percent / 100)
        
    def save(self):
        """Save product to database"""
        from database import save_to_db
        save_to_db(self)
