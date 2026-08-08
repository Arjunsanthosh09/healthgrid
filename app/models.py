# from app import login_manager, mysql
# from flask_login import UserMixin

# class User(UserMixin):
#     def __init__(self, id, full_name, email, role, status='active'):
#         self.id = id
#         self.full_name = full_name
#         self.email = email
#         self.role = role
#         self.status = status

# @login_manager.user_loader
# def load_user(user_id):
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT id, full_name, email, role FROM users WHERE id = %s", (user_id,))
#     user = cur.fetchone()
#     cur.close()
#     if user:
#         return User(id=user[0], full_name=user[1], email=user[2], role=user[3])
#     return None

# # =============================================
# # USER MODEL
# # =============================================
# class User(UserMixin):
#     def __init__(self, id, full_name, email, role, er_department_id=None):
#         self.id = id
#         self.full_name = full_name
#         self.email = email
#         self.role = role
#         self.er_department_id = er_department_id

# @login_manager.user_loader
# def load_user(user_id):
#     conn = get_db()
#     cur = conn.cursor()
#     cur.execute("SELECT id, full_name, email, role, er_department_id FROM users WHERE id = %s", (user_id,))
#     user = cur.fetchone()
#     cur.close()
#     conn.close()
#     if user:
#         return User(
#             id=user['id'], 
#             full_name=user['full_name'], 
#             email=user['email'], 
#             role=user['role'],
#             er_department_id=user.get('er_department_id')
#         )
#     return None