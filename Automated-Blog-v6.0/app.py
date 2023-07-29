from website import create_app
import stripe
import config
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta



app = create_app()

scheduler = APScheduler()
scheduler.init_app(app)

from website.models import User
from website import db


def check_memberships():
    with app.app_context():
        users = User.query.all()

        for user in users:
            try:
                stripe.api_key = config.stripe_keys["secret_key"]

                subscription_id = user.subscription_id
                print(subscription_id)
                if subscription_id != None:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    status = subscription['status']
                else:
                    continue

                if status == 'active':
                    user.blogs_remaining_this_month = config.blogs_with_membership[user.membership_level] + user.blogs_remaining_this_month
                    db.session.commit()
            except stripe.error.StripeError as e:
                print("Error:", str(e))
                scheduler.add_job(id='one_minute_task', func=check_memberships, trigger='date', run_date=datetime.now() + timedelta(seconds=30))



if __name__ == '__main__':
    scheduler.add_job(id='monthly_task', func=check_memberships, trigger='cron', day='1', month='*')
    scheduler.start()

    app.run(debug=True, use_reloader=False)