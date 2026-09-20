import { CanvasPage } from "../../../components/canvas/CanvasPage";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <CanvasPage id={id} />;
}
