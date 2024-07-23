// Importing express, a minimalist web framework for Node.js
const express = require('express');
const app = express();      // Used to set up server

// Creates HTTP server and binds it to express
const http = require('http').createServer(app);
// Initializes a new instance of socket.io by passing the HTTP server object
// Socket IO is a library that enables real time birdirectional communication
const io = require('socket.io')(http);
const port = 3000;

// Serves static files (HTML, CSS, JS) from same dir
app.use(express.static(__dirname));

// When someone visits the url, server responds by sending index.html file from curr dir
app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

// Initializes an empty object to keep track of connected users by their socket id
const users = {};

// Listens to action connection
io.on('connection', socket => {

  // On action new user, we broadcast that that person has joined
  socket.on('new-user', name => {
    users[socket.id] = name;
    socket.broadcast.emit('user-connected', name);
  });

  // On action send message, we send action chat-message
  socket.on('send-chat-message', message => {
    socket.broadcast.emit('chat-message', { message: message, name: users[socket.id] });
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