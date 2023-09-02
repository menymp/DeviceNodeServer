import React from 'react';
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min";
import logo from './logo.svg';
import './App.css';
import NavMenu from './components/Nav/Nav';


function App() {
  return (
    <>
        <NavMenu></NavMenu>
        <h1>Hello world</h1>
    </>
  );
}

export default App;
