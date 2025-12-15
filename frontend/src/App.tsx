import { Heatmap } from './components/Heatmap'
import { TooltipProvider } from './components/ui/tooltip'

function App() {
  return (
    <TooltipProvider>
      <Heatmap />
    </TooltipProvider>
  )
}

export default App
