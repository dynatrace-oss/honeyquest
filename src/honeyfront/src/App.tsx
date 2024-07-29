// Copyright 2024 Dynatrace LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Portions of this code, as identified in remarks, are provided under the
// Creative Commons BY-SA or the MIT license, and are provided without
// any warranty. In each of the remarks, we have provided attribution to the
// original creators and other attribution parties, along with the title of
// the code (if known) a copyright notice and a link to the license, and a
// statement indicating whether or not we have modified the code.

import { useMemo, useState } from "react";
import { QueryClient, QueryClientProvider } from "react-query";
import { ReactQueryDevtools } from "react-query/devtools";

import ExperimentInfo from "./components/ExperimentInfo";
import FeedbackComponent from "./components/FeedbackComponent";
import Footer from "./components/Footer";
import Main from "./components/Main";
import { userPreferences } from "./context/UserPreferences";

import { FEEDBACK_MODAL_ID } from "./types/Common";

const queryClient = new QueryClient();

function App() {
  const [fullscreen, setFullscreen] = useState(false);
  const preferences = useMemo(
    () => ({ fullscreen, setFullscreen }),
    [fullscreen, setFullscreen],
  );

  return (
    <QueryClientProvider client={queryClient}>
      <userPreferences.Provider value={preferences}>
        <ExperimentInfo disabled />
        <Main />
        <Footer />
        <FeedbackComponent modalId={FEEDBACK_MODAL_ID} />
        <ReactQueryDevtools initialIsOpen={false} />
      </userPreferences.Provider>
    </QueryClientProvider>
  );
}

export default App;
