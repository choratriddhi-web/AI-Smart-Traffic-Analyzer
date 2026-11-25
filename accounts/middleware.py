from services.mongodb import get_collection
from bson import ObjectId

class MongoAuthMiddleware:
    """
    Middleware that attaches mongo_user to the request if a user session exists.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.mongo_user = None
        user_id = None
        try:
            user_id = request.session.get('user_id')
        except Exception:
            user_id = None

        if user_id:
            try:
                users_col = get_collection('users')
                try:
                    obj_id = ObjectId(user_id)
                    user = users_col.find_one({"_id": obj_id})
                except Exception:
                    user = users_col.find_one({"_id": user_id})

                if user:
                    user['id'] = str(user['_id'])
                    request.mongo_user = user
            except Exception:
                request.mongo_user = None

        response = self.get_response(request)
        return response
