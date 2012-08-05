// Use asynchronous node.js to submit 10 transaction requests at once
// Account 227 member 259 is Krubo / Paul

var TESTSERVER = 'paul.mess.mariposa.coop'
var https = require('https')
var querystring = require('querystring')

console.log('Start')

function PostCode() {
  var post_data = querystring.stringify({
    'transaction': '{"purchase_type": "S", "account": 227, "purchase_amount": 0.01, "member": 259, "payment_amount": 0, "payment_type": "", "date": "2012-08-05 01:01:01"}'
  })
  var post_options = {
    host: TESTSERVER,
    port: 443,
    path: '/is4c/recordtransaction/?secret=is4secret',
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': post_data.length
    }    
  }
  var post_req = https.request(post_options, function(res) {
    console.log('statusCode: ', res.statusCode)
    res.setEncoding('utf8')
    res.on('data', function(chunk) {
      console.log('Response: '+chunk)
    })
  })
  post_req.write(post_data)
  post_req.end()
  console.log('Posted.')
}
for(var i = 0; i < 10; i++) {
  PostCode()
}
