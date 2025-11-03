import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { LandingPage, SignUpPage } from "./components/pages";
import { CouncilDetailPage } from "./components/pages/CouncilDetailPage";
import { ScrollToTop } from "./components/ScrollToTop";

function ScrollWrapper() {
  return (
    <>
      <ScrollToTop />
      <Outlet />
    </>
  );
}

export const router = createBrowserRouter([
  {
    element: <ScrollWrapper />,
    children: [
      { path: "/", element: <LandingPage /> },
      { path: "/signup", element: <SignUpPage /> },
      { path: "/council/:councilId", element: <CouncilDetailPage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
