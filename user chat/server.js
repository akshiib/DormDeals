// Imports
require('dotenv').config({ path: '../.env' }); // Adjust the path as needed
const express = require('express');   // web framework for Node.js
const app = express();    // Instantiating the web framework
const http = require('http').createServer(app);   // http object, binding it to app object
const io = require('socket.io')(http);    // Enabling bidirectional real time chat
const port = process.env.PORT || 3000;    // Port on which the server will listen
const { MongoClient } = require('mongodb');   // Connecting to MongoDB
const mongoUri = process.env.MONGODB_URI;   // Env variables
const dbName = process.env.DB_NAME;

// Error handling
if (!mongoUri) {
  console.error("MONGODB_URI environment variable is not set");
  process.exit(1);
}

if (!dbName) {
  console.error("DB_NAME environment variable is not set");
  process.exit(1);
}

// Replace the uri string with your connection string.
const client = new MongoClient(mongoUri);
const db = client.db(dbName);
const messagesCollection = db.collection('messages');
const chatSchema = {
  participants: [String], // Who the chat is between
  messages: [
    {
      sender: String, // User ID or username of the sender
      message: String, // The actual message text
      timestamp: Date, // When the message was sent
    }
  ]
};

function saveMessage(sender, receiver, messageText){
  const participants = [sender, receiver].sort(); 
  messagesCollection.updateOne(
    { participants: participants },   // Inserts messages where participants matches ours
    {
      $push: {
        messages: {
          sender: sender,
          message: messageText,
          timestamp: new Date()
        }
      }
    },
    { upsert: true } // if participants doesn't exist, create new doc
  );
}


function loadChatHistory(user1, user2, callback) {
  const participants = [user1, user2].sort();

  messagesCollection.findOne(
    { participants: participants },
    (err, chat) => {
      if (err) throw err;
      callback(chat ? chat.messages : []);
    }
  );
}

// Serves static files (HTML, CSS, JS) from same dir
app.use(express.static(__dirname));

// When someone visits the URL, server responds by sending index.html file from curr dir
app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

// Initializes an empty object to keep track of connected users by their socket id
const users = {};

// Listens to connection
io.on('connection', socket => {
  // On action new user, we broadcast that that person has joined
  socket.on('new-user', name => {
    users[socket.id] = name;
    socket.broadcast.emit('user-connected', name);
  });

  socket.on('load-chat-history', (receiver) => {
    const sender = users[socket.id];

    loadChatHistory(sender, receiver, (messages) => {
      socket.emit('chat-history', messages);
    });
  });

  // On action send message, we send action chat-message
  socket.on('send-chat-message', ({ receiver, message }) => {
    const sender = users[socket.id];
    saveMessage(sender, receiver, message);
    socket.broadcast.emit('chat-message', { message, name: sender });
  });

  // On action user leaving, we send action user-disconnected
  socket.on('disconnect', () => {
    socket.broadcast.emit('user-disconnected', users[socket.id]);
    delete users[socket.id];
  });
});

http.listen(port, () => {
  console.log(`Server running at http://localhost:${port}/`);
});