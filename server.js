require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const Razorpay = require('razorpay');
const crypto = require('crypto');
const cors = require('cors');

const app = express();
const port = 3000;

app.use(cors());
app.use(bodyParser.json());

const razorpay = new Razorpay({
  key_id: process.env.RAZORPAY_KEY_ID,
  key_secret: process.env.RAZORPAY_KEY_SECRET,
});

app.get('/', (req, res) => {
  res.send('Razorpay backend is running');
});

app.post('/create-order', async (req, res) => {
  const { amount } = req.body;
  try {
    const options = {
      amount,
      currency: 'INR',
      receipt: 'receipt#1',
      payment_capture: 1,
    };
    const order = await razorpay.orders.create(options);
    res.json(order);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/verify-payment', (req, res) => {
  const { razorpay_order_id, razorpay_payment_id, razorpay_signature } = req.body;
  const hmac = crypto.createHmac('sha256', process.env.RAZORPAY_KEY_SECRET);
  hmac.update(razorpay_order_id + '|' + razorpay_payment_id);
  const generatedSignature = hmac.digest('hex');
  if (generatedSignature === razorpay_signature) {
    res.json({ success: true });
  } else {
    res.json({ success: false, message: 'Invalid signature' });
  }
});

app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
