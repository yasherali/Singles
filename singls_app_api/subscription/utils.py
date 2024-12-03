from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from user_management.models import Profile
from rest_framework import status
from .models import Membership

def create_subscription(user_obj,profile_obj,customer_obj,plan_obj,charges_type, billing_cycle=None):
    response = {'status': False}
    time_period = 1
    try:
        if billing_cycle is not None:
            billing_cycle = 'monthly'
            time_period = 1
        else:
            billing_cycle = "monthly"
        current_date = timezone.now()
        next_date =current_date + relativedelta(months=+time_period)
        subscriptions_obj_qs = Membership.objects.filter(i_profile=customer_obj.i_profile)
        if len(subscriptions_obj_qs) != 0:
            for subscriptions_obj in subscriptions_obj_qs:
                subscriptions_obj.is_active = False
                subscriptions_obj.save()
        with transaction.atomic():
            sub_month_cycle = None
            if billing_cycle == 'monthly':
                sub_month_cycle = 'monthly'
            else:
                sub_month_cycle = 'annually'
            subscriptions_obj =  Membership.objects.create(i_plan = plan_obj,
                                    i_profile=customer_obj.i_profile,starts_at=current_date,
                                    ends_at = next_date,is_active =False,
                                    billing_cycle = 'monthly')
            resp = create_subscription_invoice(user_obj,subscriptions_obj,customer_obj,plan_obj,charges_type, 'monthly')
            print("create_subscription_invoice response:",resp)
            if resp['status'] == True:
                subscriptions_obj.is_active =True
                subscriptions_obj.save()
                response = {'status': True,'message': 'Membership created successfully'}
                type = "subscription"
                # only_user_notification("Membership has been created","Membership", profile_obj.pk, type)

            else:
                response = {'status': False,'error': 'error occurred while Invoicing and payment'}
                
    except Exception as e:
        import sys, os
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        response = {'status': False,'error': repr(e)}
    return response



def create_user_subscription(data):
    response = {'status': False}
    email =  data.get('email')
    print(email)
    # password =  data.get('password')
    card_token =  data.get('card_token')
    plan_id =  data.get('plan')
    charges_type = data.get('charges_type')
    print('card_token', card_token)
    print('plan_id' , plan_id)
    try:
        with transaction.atomic():
            plan_obj =  Plan.objects.get(pk = plan_id)
            print(plan_obj)
            user_obj = User.objects.get(email=email)
            print(user_obj)
            try:
                profile_obj = Profile.objects.get(user=user_obj, role='recruiter')
            except Profile.DoesNotExist:
                response['error'] = 'This user is not a recruiter'
                return response
            customer_obj = create_customer_object(user_obj,card_token)
            print("Customer: ",customer_obj)
            res = create_subscription(user_obj,profile_obj,customer_obj,plan_obj, charges_type)
            print("Res: ",res)
            if res['status'] == True:
                user_obj.is_active =True
                user_obj.save()
                response = {'status': True,'message': 'Membership updgraded successfully'}
            else:
                response = {'status': False,'error': 'error occurred while Invoicing and payment'}
    except Exception as e:
        print("Error Occured: ",repr(e))
        response['error'] = repr(e)
    return response

def get_user_subscription(user):
    list_of_user_subscription = []
    profile_obj = Profile.objects.get(user=user)
    customer_obj = Customer.objects.get(i_profile = profile_obj)
    subs_obj =  Membership.objects.filter(i_profile = customer_obj.i_profile,is_active = True).values()
    for subs in subs_obj:
        list_of_user_subscription.append(subs)
    for i in list_of_user_subscription:
        i['profile_id_id'] = customer_obj.i_profile.user.email
        # print(invoice['i_plan_id'])-
        plan_obj =  Plan.objects.get(pk = i["i_plan_id"])
        i['plan_id_id'] = plan_obj.name
    return list_of_user_subscription

def get_driver_subscription(user):
    resp = {"status": False,"message":"No Subscription Found",
            "data": None, "status_code": 400}
    try:
        qs = Membership.objects.filter(i_profile = user.profile,is_active = True)
        if qs:
            obj = qs.last()
            billing_cycle =  obj.billing_cycle if obj.billing_cycle == 'monthly' else 'yearly'
            resp['data']={
                'name' : f"{billing_cycle} {obj.i_plan.name}",
                "billing_cycle": billing_cycle,"plan_id": obj.i_plan.pk,
                "starts_at": obj.starts_at,"ends_at": obj.ends_at,
                "product_id" : obj.product_id}
            resp['status']=True
            resp['status_code']=200
            resp['message']="Driver Active membership found"
    
    except Exception as e:
            resp['message'],resp['status'],resp['status_code'],resp['data'] = repr(e),False,400,None
    return resp

def get_plan_of_customer(profile):
    try:
        customer_id = Customer.objects.get(i_profile = profile)
        membership = Membership.objects.filter(i_profile = customer_id.i_profile, is_active = True)
        if membership.exists():
            membership = membership.last()
            return membership.i_plan.pk
        return None
    except:
        return None
    
def create_subscription_only(user_obj,plan_obj = None,billing_cycle=None,
                             product_id = None,reference_id=None,provider =  None,amount = None):
    
    response = {'status': False, 'status_code': 400,
                'message': "Default response message", 'data': None}
    # ('yearly','monthly')
    time_period = 0
    message = 'memebership created successfully'
    current_date = timezone.now()
    amount = 0 if amount is None else amount
    try:
        time_period = 1 if billing_cycle is None or billing_cycle == 'monthly' else 12
        billing_cycle = billing_cycle if billing_cycle is None or billing_cycle == 'monthly' else 'annually'
        next_date = current_date + relativedelta(months=+time_period)
            # next_date = datetime.strptime("2099-12-31", "%Y-%m-%d")
        subscriptions_obj_qs = Membership.objects.filter(i_profile = user_obj.profile)
        if subscriptions_obj_qs:
            subscriptions_obj_qs.update(is_active = False)
            message = 'memebership update successfully'
        with transaction.atomic():
            obj = Membership.objects.create(i_plan = plan_obj,
                i_profile = user_obj.profile,starts_at=current_date,
                ends_at = next_date,is_active = True,
                billing_cycle = billing_cycle,reference_id = reference_id,
                provider = provider,amount = amount ,
                product_id = product_id)
            next_date = current_date + relativedelta(months=+1)
            
        response['status']=True 
        response['status_code']=200
        response['message']=message 
        response['data']= None

    except Exception as e:
        response['message']=repr(e)
    
    return response

def get_driver_active_membership(profile):
    response = {"status": False, "data": None}
    qs = Membership.objects.filter(i_profile = profile,is_active = True)
    if qs.exists():
        response['status'] = True
        response['data']=qs.last()
    return response

from functools import reduce
from datetime import datetime
import calendar

def get_driver_apply_status(membership_obj):
    response = {"status": False, "data": None}
    obj = membership_obj.membership_modules.filter(i_plan_module__i_module__name="apply_job_per_month").last()
    if obj.expired_at < timezone.now():
        last_date = reduce(lambda x, y: y[1], [calendar.monthrange(datetime.now().year, datetime.now().month)], None)
        next_date = timezone.now().date().replace(day=last_date)
        if next_date <= timezone.now().date():
            next_date = timezone.now() + relativedelta(months=+1)
        obj.expired_at = next_date
        obj.consumed_units = 0
        obj.save()
    response['status'] = obj.consumed_units < obj.i_plan_module.allowed_units
    response['data'] = obj
    return response

def create_one_time_invoice(profile_obj,meta):
    # meta data yahan dalega kuch '
    response = {"status": False,"data": None}
    resp = get_driver_active_membership(profile_obj)
    if resp['status']:
        membership_obj = resp['data']
        price = membership_obj.i_plan.plan_charges.filter(code="job").last().price #0.99
        inv_obj = Invoice.objects.create(amount =price,is_paid=True)
        inv_obj.invoice_number = inv_obj.get_invoice_number()
        inv_obj.save()
        payment_obj = Payment.objects.create(i_invoice=inv_obj,amount=price)
        obj = membership_obj.membership_modules.filter(i_plan_module__i_module__name="apply_job_per_month").last()
        obj.consumed_units -= 1
        obj.save()
        response['status'] =True
        response['data'] =inv_obj
    return response
    


def create_guest_recruiter_customer(data):
    response = {'status': False}
    email =  data.get('email')
    print(email)
    # password =  data.get('password')
    card_token =  data.get('card_token')
    try:
        with transaction.atomic():
            user_obj = User.objects.get(email=email)
            print(user_obj)
            try:
                profile_obj = Profile.objects.get(user=user_obj, role='recruiter')
            except Profile.DoesNotExist:
                response['error'] = 'This user is not a recruiter'
                return response
            customer_obj = create_customer_object(user_obj,card_token)
            print("Customer: ",customer_obj)
            response = {"status" : True, "status_code" : status.HTTP_200_OK, "message" : "Customer Created Successfully", "data" : {}}
    except Exception as e:
        print("Error Occured: ",repr(e))
        response['error'] = repr(e)
    return response