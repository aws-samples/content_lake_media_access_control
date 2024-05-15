// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { Route, Routes, Navigate } from "react-router-dom"
import Lockers from './pages/Lockers';
import EditList from './pages/EditList';
import EditDetails from './pages/EditDetails';
import AuthProvider from './components/AuthProvider';
import './App.css';

function App() {
  
  return (
    <AuthProvider>
      <div className="App">
        <Routes>
          <Route path="/lockers" element={<Lockers/>} />
          <Route path="/lockers/:locker" element={<EditList />} />
          <Route path="/lockers/:locker/edits/:editId" element={<EditDetails />} />
          <Route path="*" element={<Navigate to="/lockers" />} />
        </Routes>
      </div>
    </AuthProvider>
  );
}

export default App;
