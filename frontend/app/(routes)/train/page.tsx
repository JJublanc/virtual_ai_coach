// app/train/page.tsx
'use client'

import { useState } from 'react'
import { VideoPlayer } from '@/components/video/VideoPlayer'
import { ExerciseList } from '@/components/exercises/ExerciseList'
import { AIAssistant } from '@/components/controls/AIAssistant'
import { QuickSetup } from '@/components/controls/QuickSetup'
import { ParameterizedSetup } from '@/components/controls/ParameterizedSetup'
import { useTrainingStore } from '@/store/trainingStore'

type AccordionSection = 'quick' | 'parameterized' | 'ia' | null

export default function TrainPage() {
  const { session, player } = useTrainingStore()
  const [openSection, setOpenSection] = useState<AccordionSection>('quick')

  const toggleSection = (section: AccordionSection) => {
    setOpenSection(openSection === section ? null : section)
  }

  return (
    <div className="flex flex-col lg:flex-row gap-6 p-4 md:p-6 bg-gray-50 min-h-screen">
      {/* Colonne gauche - Vidéo + Exercices */}
      <div className="flex-1 space-y-4 w-full lg:w-auto">
        <VideoPlayer />
        <ExerciseList />
      </div>

      {/* Colonne droite - Contrôles */}
      <div className="w-full lg:w-[400px] space-y-4 flex-shrink-0 max-h-screen overflow-y-auto pb-6 sticky top-0">
        <AIAssistant />

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <label className="block text-sm text-gray-600 mb-2">Training duration</label>
          <input
            type="number"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
            placeholder="Minutes"
          />
        </div>

        {/* Quick Setup - Accordion */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('quick')}
            className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <h3 className="text-sm font-medium">Quick setup</h3>
            <svg
              className={`w-4 h-4 text-gray-400 transition-transform ${openSection === 'quick' ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {openSection === 'quick' && (
            <div className="px-4 pb-4">
              <QuickSetup />
            </div>
          )}
        </div>

        {/* Parameterized - Accordion */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('parameterized')}
            className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <h3 className="text-sm font-medium">Parameterized</h3>
            <svg
              className={`w-4 h-4 text-gray-400 transition-transform ${openSection === 'parameterized' ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {openSection === 'parameterized' && (
            <div className="px-4 pb-4">
              <ParameterizedSetup />
            </div>
          )}
        </div>

        {/* IA Assisted - Accordion */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('ia')}
            className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <h3 className="text-sm font-medium">IA assisted</h3>
            <svg
              className={`w-4 h-4 text-gray-400 transition-transform ${openSection === 'ia' ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {openSection === 'ia' && (
            <div className="px-4 pb-4">
              <textarea
                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm text-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-gray-900"
                rows={3}
                placeholder="Just describe how you feel and the type of training you want to do. Your coach will prepare a personalized session for you."
              />
            </div>
          )}
        </div>

        <button className="w-full py-4 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-colors">
          Generate training
        </button>
      </div>
    </div>
  )
}
