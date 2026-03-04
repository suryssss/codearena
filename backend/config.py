class Config:
    SECRET_KEY = "supersecret"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:Rishika@11@localhost:5432/codejudge"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "jwt-secret"