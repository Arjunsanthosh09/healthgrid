from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
password = 'Admin@123'  # Change this to your desired password
hashed = bcrypt.generate_password_hash(password).decode('utf-8')
print(hashed)

# admin@healthgrid.com