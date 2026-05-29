import { useState } from 'react'
import Header from './components/Header'
import Tabs, { TabKey } from './components/Tabs'
import ChatTab from './components/ChatTab'
import UploadTab from './components/UploadTab'
import Notifications from './components/Notifications'

export default function App() {
  const [tab, setTab] = useState<TabKey>('chat')
  return (
    <div className="app">
      <Header />
      <Tabs value={tab} onChange={setTab} />
      <div className="tab-pane" style={tab === 'upload' ? undefined : { display: 'none' }}>
        <UploadTab />
      </div>
      <div className="tab-pane" style={tab === 'chat' ? undefined : { display: 'none' }}>
        <ChatTab />
      </div>
      <Notifications />
    </div>
  )
}
