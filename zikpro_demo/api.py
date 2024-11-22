import jwt
import frappe
from datetime import datetime, timedelta

# Secret key for signing JWT
SECRET_KEY = '43d4f2888b3a5d9'
def generate_jwt_token(user):
    # the token expiration
    expiration = datetime.utcnow() + timedelta(hours=1)
    
    # the payload of the JWT
    payload = {
        'user': user,
        'exp': expiration
    }
    
    # Generate JWT token
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

@frappe.whitelist(allow_guest=True)
def get_jwt_token():
    #  the user which will authenticate automatically
    user = 'nabeel.khan@zikpro.com'
'  
    
    #  JWT token for the user
    token = generate_jwt_token(user)
    
    # Return the token as a JSON response
    return {
        'token': token
    }
@frappe.whitelist(allow_guest=True)
def jwt_login(token):
    try:
        # Decode and verify the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        # Get the user from the token payload
        user = payload.get('user')
        
        if not user:
            frappe.throw("Invalid token.")
        
        # Log in the user
        frappe.set_user(user)
        
        # set the session to ensure it's applied for future requests
        frappe.local.login_manager.user = user
        frappe.local.login_manager.post_login()
        
        # Redirect to the ERPNext desk page
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/app"
        
    except jwt.ExpiredSignatureError:
        frappe.throw("Token has expired.")
    except jwt.InvalidTokenError:
        frappe.throw("Invalid token.")


@frappe.whitelist(allow_guest=True)
def get_available_slots(date):

    available_slots = []

    if not date:
        return{
            "available_slots" : [],
            "message": "Please select a date"
        }

    available_slot = frappe.get_all("Available Schedule",filters = {"date": date},fields=["name"])

    if not available_slot:
        return{
            "available_slots": [],
            "message": "No slot available for the specific date"
        }

    time_slots = frappe.get_all("Appointment Slot",filters = {"parent": available_slot[0]['name']},fields=["start_time","end_time"])

    if not time_slots:
        return{
            "available_slots": [],
            "message": "No slot available for the specific date"
        }

    available_slots = [f"{slot['start_time']} - {slot['end_time']}" for slot in time_slots]

    return{
        "available_slots": available_slots,
        "message": ""
    }

@frappe.whitelist(allow_guest=True)
def send_demo_schedule_email(slot, date, email, message):
    try:
        if frappe.db.exists("Demo Schedule", {"slot": slot, "date": date}):
            return 'slot_taken'  

        demo_schedule = frappe.get_doc({
            "doctype": "Demo Schedule",
            "date": date,
            "slot": slot,
            "email": email,
            "message": message
        })
        demo_schedule.insert()

        recipients = [email, "demo@zikpro.com"]
        subject=f"Demo Scheduled on {date}"
        # email_content=f"""
        #     A new demo has been scheduled:
        #     Date: {date}
        #     Time Slot: {slot}
        #     Message: {message}
        # """

        email_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h2 style="color: #4CAF50; text-align: center;">Demo Scheduled</h2>
            <p style="font-size: 16px; color: #333;">
                Hi there,<br><br>
                A new demo has been scheduled. Here are the details:
            </p>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Date:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{date}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Time Slot:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{slot}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Message:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{message if message else 'No additional message'}</td>
                </tr>
            </table>
            <p style="font-size: 16px; color: #333;">
                <br><br>
                Best regards,<br>
                Zikpro Pvt. Ltd.
            </p>
        </div>
        """

        frappe.sendmail(recipients = recipients,subject=subject,message=email_content,delayed=False)
        return 'success'

    except Exception as e:
        frappe.log.error(frappe.get_traceback(),'Demo Email Send Error')
        return 'failure'


