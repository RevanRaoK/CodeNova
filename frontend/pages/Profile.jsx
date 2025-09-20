import React from 'react'
import {
  UserIcon,
  MailIcon,
  KeyIcon,
  LogOutIcon,
  CameraIcon,
} from 'lucide-react'
export function Profile() {
  return (
    <div className="w-full">
      <h1 className="text-2xl font-bold mb-6">Profile</h1>
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="md:flex">
          {/* Left sidebar with profile info */}
          <div className="md:w-80 bg-gray-50 p-6 border-b md:border-b-0 md:border-r border-gray-200">
            <div className="flex flex-col items-center text-center">
              <div className="relative">
                <div className="w-32 h-32 rounded-full bg-indigo-100 flex items-center justify-center border-4 border-white shadow">
                  <UserIcon className="h-16 w-16 text-indigo-500" />
                </div>
                <button className="absolute bottom-0 right-0 bg-indigo-600 p-2 rounded-full text-white">
                  <CameraIcon className="h-4 w-4" />
                </button>
              </div>
              <h2 className="mt-4 text-xl font-semibold text-gray-900">
                John Developer
              </h2>
              <p className="text-gray-500">Senior Software Engineer</p>
              <div className="mt-6 w-full">
                <div className="flex items-center py-3 border-b border-gray-200">
                  <MailIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-gray-600">john.dev@example.com</span>
                </div>
                <div className="flex items-center py-3">
                  <KeyIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-gray-600">
                    Account active since Jan 2023
                  </span>
                </div>
              </div>
              <button className="mt-6 flex items-center text-red-600 hover:text-red-800">
                <LogOutIcon className="h-5 w-5 mr-2" />
                Sign out
              </button>
            </div>
          </div>
          {/* Main profile content */}
          <div className="flex-1 p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-6">
              Account Information
            </h2>
            <form className="space-y-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label
                    htmlFor="first-name"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    First name
                  </label>
                  <input
                    type="text"
                    id="first-name"
                    className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    defaultValue="John"
                  />
                </div>
                <div>
                  <label
                    htmlFor="last-name"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Last name
                  </label>
                  <input
                    type="text"
                    id="last-name"
                    className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    defaultValue="Developer"
                  />
                </div>
              </div>
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  defaultValue="john.dev@example.com"
                />
              </div>
              <div>
                <label
                  htmlFor="job-title"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Job title
                </label>
                <input
                  type="text"
                  id="job-title"
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  defaultValue="Senior Software Engineer"
                />
              </div>
              <div>
                <label
                  htmlFor="bio"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Bio
                </label>
                <textarea
                  id="bio"
                  rows={4}
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  defaultValue="Experienced developer focused on building scalable applications and improving code quality."
                />
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Programming Languages
                </h3>
                <div className="space-y-4">
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="javascript"
                        name="languages"
                        type="checkbox"
                        defaultChecked
                        className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label
                        htmlFor="javascript"
                        className="font-medium text-gray-700"
                      >
                        JavaScript
                      </label>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="typescript"
                        name="languages"
                        type="checkbox"
                        defaultChecked
                        className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label
                        htmlFor="typescript"
                        className="font-medium text-gray-700"
                      >
                        TypeScript
                      </label>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="python"
                        name="languages"
                        type="checkbox"
                        className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label
                        htmlFor="python"
                        className="font-medium text-gray-700"
                      >
                        Python
                      </label>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="java"
                        name="languages"
                        type="checkbox"
                        className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label
                        htmlFor="java"
                        className="font-medium text-gray-700"
                      >
                        Java
                      </label>
                    </div>
                  </div>
                </div>
              </div>
              <div className="pt-5">
                <div className="flex justify-end">
                  <button
                    type="button"
                    className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Save
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
