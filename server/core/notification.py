from flask import Blueprint, g, make_response, abort, request
from core.permission import auth
import json

notification = Blueprint("notification", __name__)

@notification.route('/notification/latest', methods=['GET'])
@auth.login_required
def get_latest_notifications():
    cur = g.db.cursor()
    cur.execute("SELECT Body, Link, unix_timestamp(CreateAt) FROM Notification \
        WHERE UserId = %s ORDER BY CreateAt DESC LIMIT 10", (str(g.user_id),))
    notifications_data = cur.fetchall()

    resp_body = []
    for notification_data in notifications_data:
        resp_body.append({
            "body": notification_data[0],
            "url": notification_data[1],
            "timestamp": notification_data[2]
        })

    resp = make_response(json.dumps(resp_body), 200)
    resp.headers["Content-Type"] = "application/json"
    return resp

@notification.route('/notification/all', methods=['GET'])
@auth.login_required
def get_all_notifications():
    cur = g.db.cursor()
    cur.execute("SELECT Body, Link, unix_timestamp(CreateAt) FROM Notification \
        WHERE UserId = %s ORDER BY CreateAt DESC", (str(g.user_id),))
    notifications_data = cur.fetchall()

    resp_body = []
    for notification_data in notifications_data:
        resp_body.append({
            "body": notification_data[0],
            "url": notification_data[1],
            "timestamp": notification_data[2]
        })

    resp = make_response(json.dumps(resp_body), 200)
    resp.headers["Content-Type"] = "application/json"
    return resp

def send_notification(user_id, body, url):
    cur = g.db.cursor()
    cur.execute("INSERT INTO Notification(UserId, Body, Link) VALUES \
        (%s, %s, %s)", (str(user_id), body, url))
    g.db.commit()

def send_following_notification(follower_user_id, following_user_id):
    cur = g.db.cursor()
    cur.execute("SELECT Nickname FROM User WHERE UserId = %s", (str(follower_user_id),))

    follower_nickname = cur.fetchone()[0]
    body = "%s started following you" % follower_nickname
    url = "/user/%d" % follower_user_id

    send_notification(following_user_id, body, url)

def send_product_comment_notification(from_user_id, product_id):
    cur = g.db.cursor()
    cur.execute("SELECT Nickname FROM User WHERE UserId = %s", (str(from_user_id),))
    from_nickname = cur.fetchone()[0]

    cur.execute("SELECT Name, UserId FROM Product WHERE ProductId = %s", (str(product_id),))
    product_data = cur.fetchone()
    product_name = product_data[0]
    seller_user_id = product_data[1]

    body = "%s posted a comment to %s" % (from_nickname, product_name)
    url = "/product/%d" % product_id

    send_notification(seller_user_id, body, url)

def send_product_comment_response_notification(comment_id):
    cur = g.db.cursor()
    cur.execute("SELECT Comment.UserId, Product.ProductId, Product.Name FROM Comment, Product \
        WHERE Comment.CommentId = %s AND Comment.ProductId = Product.ProductId", (str(comment_id),))
    comment_data = cur.fetchone()

    user_id = comment_data[0]
    product_id = comment_data[1]
    product_name = comment_data[2]

    body = "Seller responed to your comment for %s" % product_name
    url = "/product/%d" % product_id

    send_notification(user_id, body, url)

def send_message_notification(from_user_id, to_user_id, content):
    cur = g.db.cursor()
    cur.execute("SELECT Nickname FROM User WHERE UserId = %s", (str(from_user_id),))

    from_nickname = cur.fetchone()[0]
    body = "%s sent message to you: \"%s...\"" % (from_nickname, content[:15])
    url = "/mybids?user_id=%d" % from_user_id

    send_notification(to_user_id, body, url)

def send_bid_response_notification(seller_user_id, bidder_user_id, bid_id, action):
    cur = g.db.cursor()

    cur.execute("SELECT Nickname FROM User WHERE UserId = %s", (str(seller_user_id),))
    seller_nickname = cur.fetchone()[0]

    cur.execute("SELECT Product.Name FROM Product, Bid WHERE Bid.BidId = %s \
        AND Bid.ProductId = Product.ProductId", (str(bid_id),))
    product_name = cur.fetchone()[0]

    body = "%s %s your bid for %s" % (seller_nickname, action, product_name)
    url = "/mybids?bid_id=%d" % bid_id

    send_notification(bidder_user_id, body, url)

def send_bid_request_notification(bidder_user_id, bid_id):
    cur = g.db.cursor()

    cur.execute("SELECT Nickname FROM User WHERE UserId = %s", (str(bidder_user_id),))
    bidder_nickname = cur.fetchone()[0]

    cur.execute("SELECT Product.Name, Product.UserId FROM Product, Bid WHERE Bid.BidId = %s \
        AND Bid.ProductId = Product.ProductId", (str(bid_id),))
    product_data = cur.fetchone()
    product_name = product_data[0]
    seller_user_id = product_data[1]

    body = "%s placed a bid for %s" % (bidder_nickname, product_name)
    url = "/mybids?bid_id=%d" % bid_id

    send_notification(seller_user_id, body, url)

def send_wantlist_notification(product_id):
    cur = g.db.cursor()

    cur.execute("SELECT ProductId, Name FROM Product WHERE ProductId = %s", (str(product_id),))
    product_data = cur.fetchone()
    product_id = product_data[0]
    product_name = product_data[1]

    body = "Product you may like: %s" % product_name
    url = "/product/%d" % product_id

    cur.execute("SELECT DISTINCT Wantlist.UserId FROM Wantlist, Product \
        WHERE Product.Name LIKE CONCAT('%%', Wantlist.Name, '%%') AND Product.ProductId = %s", (str(product_id),))
    wantlists_data = cur.fetchall()

    for wantlist_data in wantlists_data:
        send_notification(wantlist_data[0], body, url)