import { useState } from 'react'
import Header from './components/Header'
import Tabs, { TabKey } from './components/Tabs'
import ChatTab from './components/ChatTab'
import UploadTab from './components/UploadTab'

export default function App() {
  const [tab, setTab] = useState<TabKey>('chat')
  return (
    <div className="app">
      <Header />
      <Tabs value={tab} onChange={setTab} />
      {tab === 'upload' ? <UploadTab /> : <ChatTab />}
    </div>
  )
}
